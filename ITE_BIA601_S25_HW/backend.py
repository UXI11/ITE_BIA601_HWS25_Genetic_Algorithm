
# backend.py - Core Logic for the Intelligent Recommendation System
# This file contains all the data processing, feature engineering,
# K-Means clustering, and Genetic Algorithm (GA) functions.
# It is the calculation heart of the project — no UI code here.


import os
import random
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


# ---- Data Loading ----
# This function reads the four Excel source files from the data folder.
# It keeps the file I/O separate from the UI so app.py stays clean.
def load_data(data_dir="data"):
    """Load raw data tables from Excel files in the given directory."""
    users = pd.read_excel(os.path.join(data_dir, "users.xlsx"))
    products = pd.read_excel(os.path.join(data_dir, "products.xlsx"))
    ratings = pd.read_excel(os.path.join(data_dir, "ratings.xlsx"))
    behavior = pd.read_excel(os.path.join(data_dir, "behavior.xlsx"))
    return users, products, ratings, behavior


# ---- Data Cleaning ----
# This function handles missing values so later steps don't break.
# - Age and price: filled with the median (a safe central value)
# - Country and category: filled with default text values
# - Ratings with missing keys are dropped entirely
# - Behavior flags (viewed, clicked, purchased) default to 0
def clean_data(users, products, ratings, behavior):
    """Clean and stabilize all DataFrames before feature building."""
    users['age'] = users['age'].fillna(users['age'].median())
    users['country'] = users['country'].fillna('Unknown')
    products['price'] = products['price'].fillna(products['price'].median())
    products['category'] = products['category'].fillna('General')
    
    ratings = ratings.dropna(subset=['user_id', 'product_id', 'rating'])
    behavior = behavior.fillna({'viewed': 0, 'clicked': 0, 'purchased': 0})
    return users, products, ratings, behavior


# ---- Feature Engineering ----
# This function transforms the raw records into derived features that
# the clustering and GA can work with. It builds two feature tables:
#   u_feat: user-level features (behavior totals, avg rating, top category)
#   p_feat: product-level features (purchase count, views, avg rating)
# It also creates implicit_score — a weighted behavior value that
# combines viewed, clicked, and purchased into one number.
def create_features(users, products, ratings, behavior):
    """Build user and product feature representations from raw data."""

    # Aggregate user behavior: total views, clicks, and purchases per user
    u_beh = behavior.groupby('user_id').agg(
        total_views=('viewed', 'sum'),
        total_clicks=('clicked', 'sum'),
        total_purchases=('purchased', 'sum')
    ).reset_index()
    
    # Calculate each user's average rating from the ratings table
    u_rat = ratings.groupby('user_id')['rating'].mean().reset_index(name='avg_rating')

    # Merge behavior and rating stats with the users table to create u_feat
    u_feat = users.merge(u_beh, on='user_id', how='left').merge(u_rat, on='user_id', how='left').fillna(0)
    
    # Find the most viewed category for each user (their top preference)
    merged = behavior.merge(products[['product_id', 'category']], on='product_id', how='left')
    cat_pref = merged[merged['viewed'] == 1].groupby(['user_id', 'category']).size().reset_index(name='count')
    
    if len(cat_pref) > 0:
        idx = cat_pref.groupby('user_id')['count'].idxmax()
        top_cats = cat_pref.loc[idx, ['user_id', 'category']].rename(columns={'category': 'top_category'})
        u_feat = u_feat.merge(top_cats, on='user_id', how='left')
    else:
        u_feat['top_category'] = 'Unknown'
        
    u_feat['top_category'] = u_feat['top_category'].fillna('Unknown')
    
    # Aggregate product-level behavior: total purchases and views per product
    p_beh = behavior.groupby('product_id').agg(
        prod_purchases=('purchased', 'sum'),
        prod_views=('viewed', 'sum')
    ).reset_index()
    
    # Calculate each product's average rating
    p_rat = ratings.groupby('product_id')['rating'].mean().reset_index(name='prod_avg_rating')

    # Merge to create p_feat with all product features in one table
    p_feat = products.merge(p_beh, on='product_id', how='left').merge(p_rat, on='product_id', how='left').fillna(0)
    
    ### Based on the research: We use Behavioral Fitness 
    ### to maximize user satisfaction score through purchase and click weights (5, 2, 1).
    # implicit_score turns the three actions into one number the GA fitness can use directly
    behavior['implicit_score'] = behavior['purchased']*5 + behavior['clicked']*2 + behavior['viewed']*1
    
    return u_feat, p_feat, behavior


# ---- K-Means User Clustering ----
### Applying the Hybrid Model mentioned in the research: Integrating clustering
### (K-means) with Genetic Optimization (GA) to increase accuracy.
# This function groups users into clusters based on their numeric features.
# StandardScaler normalizes the data first so no single feature dominates.
# The cluster label becomes part of the user's identity and is used later
# by the fitness function to limit the search space (Search Space Reduction).
def cluster_users(user_features, n_clusters=4):
    """Cluster users into groups using K-Means on their behavioral features."""
    features = user_features[['age', 'total_views', 'total_clicks', 'total_purchases', 'avg_rating']].copy()
    scaler = StandardScaler()
    scaled_f = scaler.fit_transform(features)
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    user_features['cluster'] = kmeans.fit_predict(scaled_f)
    return user_features, kmeans

# GENETIC ALGORITHM (GA) FUNCTIONS
# The GA simulates natural evolution to find the best product
# recommendations. Each "chromosome" is a list of product IDs.

# ---- Population Initialization ----
# Generate an initial random population composed of a set of chromosomes.
# Each chromosome is a list of 'top_n' unique product IDs.
# random.sample ensures no repeated products in the same chromosome.
def ga_init_pop(all_products, pop_size, top_n):
    """Create the first random population of chromosomes."""
    return [random.sample(all_products, top_n) for _ in range(pop_size)]


# ---- Fitness Function ----
# Evaluate how good a chromosome (product list) is for a specific user.
# The score is based on multiple factors:
#   - Category match: +5 if product matches user's top category
#   - Rating weight: product's average rating multiplied by 2
#   - Cluster behavior: implicit_score from similar users (log-scaled to avoid extremes)
#   - Diversity bonus: reward for having different categories in the list
### Based on research: We apply "Search Space Reduction" using clusters to
### train the GA on the behavior of similar users only.
def ga_fitness(chromosome, target_user_id, user_features, product_features, behavior, top_n):
    """Calculate the fitness score for a single chromosome."""
    user_info = user_features[user_features['user_id'] == target_user_id].iloc[0]
    user_cat = user_info['top_category']
    user_cluster = user_info['cluster']
    
    ### Search Space Reduction: Extract cluster users only to reduce search scope
    cluster_users = user_features[user_features['cluster'] == user_cluster]['user_id']
    ### Application of research: Limit behavior data to the cluster's "interaction space" for increased accuracy and speed
    c_behavior = behavior[behavior['user_id'].isin(cluster_users)]
    
    score = 0
    categories = set()
    for pid in chromosome:
        prod_info = product_features[product_features['product_id'] == pid].iloc[0]
        cat = prod_info['category']
        categories.add(cat)

        # Give a bonus if this product's category matches the user's favorite
        if cat == user_cat: score += 5

        # Add weight from the product's general average rating
        score += prod_info['prod_avg_rating'] * 2

        # Add cluster-level implicit behavior score (log-scaled to prevent large outliers)
        cluster_impl = c_behavior[c_behavior['product_id'] == pid]['implicit_score'].sum()
        score += np.log1p(cluster_impl) * 1.5
        
    # Diversity reward: more unique categories in the chromosome = higher score
    diversity = len(categories) / top_n
    score += diversity * 5
    return max(0.1, score) # Ensure positive value for roulette wheel


# ---- Selection (Roulette Wheel) ----
# Roulette Wheel Selection: Probability is directly proportional to fitness.
# Better chromosomes have a higher chance of being selected as parents,
# but weaker ones still have a small chance — this keeps exploration alive.
def ga_selection(population, fitness_scores):
    """Select two parents from the population using roulette wheel method."""
    total_f = sum(fitness_scores)
   
    # Calculate selection probability for each individual [Page 17]
    probs = [f/total_f for f in fitness_scores]
    
    # Select two individuals (parents) for the crossover process according to their fitness ratio
    parents_indices = np.random.choice(len(population), size=2, p=probs, replace=False)
    return population[parents_indices[0]], population[parents_indices[1]]


# ---- Crossover (1-Point) ----
# Implementation of (1-point crossover) at a random point by exchanging chromosome segments.
# With probability Pc=0.8, it splits two parents and combines their genes.
# After combining, we remove duplicates to keep recommendations unique.
def ga_crossover(p1, p2, top_n):
    """Perform 1-point crossover between two parent chromosomes."""
    if random.random() < 0.8: # Pc - Crossover probability (0.6 - 0.9) [Page 9-10]
        point = random.randint(1, top_n - 1)
        child = p1[:point] + p2[point:]
        # Ensure no duplication in suggestions (Constraint handling)
        child = list(dict.fromkeys(child))
        while len(child) < top_n:
            child.append(random.choice(p1 + p2))
            child = list(dict.fromkeys(child))
        return child
    return p1[:]


# ---- Mutation ----
# Change a specific gene with low probability Pm to ensure diversity.
# This prevents the population from converging too early on one solution.
# After mutation, duplicates are removed again to keep the list valid.
def ga_mutate(chrom, all_products, mutation_rate, top_n):
    """Apply random mutation to a chromosome's genes."""
    for i in range(len(chrom)):
        if random.random() < mutation_rate:
            chrom[i] = random.choice(all_products)
    
    # Remove any duplicate elements to ensure product diversity in recommendation
    chrom = list(dict.fromkeys(chrom))
    while len(chrom) < top_n:
        chrom.append(random.choice(all_products))
        chrom = list(dict.fromkeys(chrom))
    return chrom


# ---- GA Optimization Loop ----
# This is the main evolution loop that brings everything together.
# It runs for a set number of generations. In each generation:
#   1. Evaluate fitness for all chromosomes
#   2. Track the best solution found so far (global best)
#   3. Keep the best chromosome (Elitism)
#   4. Build a new population using Selection → Crossover → Mutation
# The goal is to reach the Global Optimum and avoid local solutions.
def ga_optimize(target_user_id, user_features, product_features, behavior, pop_size=20, generations=10, mutation_rate=0.1, top_n=5):
    """Run the full Genetic Algorithm to find the best recommendation list."""
    all_products = product_features['product_id'].tolist()
    pop = ga_init_pop(all_products, pop_size, top_n)
    best_chrom = None
    global_best = -1
    history = []
    
    # Iterating generations to search for the optimal solution
    for gen in range(generations):
        # Evaluate fitness for every chromosome in the current population
        fitness_scores = [ga_fitness(chrom, target_user_id, user_features, product_features, behavior, top_n) for chrom in pop]
        
        # Save the best solution in the current generation
        curr_best_f = max(fitness_scores)
        history.append(curr_best_f)
        if curr_best_f > global_best:
            global_best = curr_best_f
            best_chrom = pop[fitness_scores.index(curr_best_f)]
            
        new_pop = []
        # Retain the best elements (Elitism) to ensure they are not lost in the next generation
        new_pop.append(best_chrom) 
        
        # Build new generation via Selection, Crossover, and Mutation
        while len(new_pop) < pop_size:
            # 3.4 Selection (Roulette Wheel)
            parent1, parent2 = ga_selection(pop, fitness_scores)
            
            # Perform Crossover to produce new solutions from the parents
            child = ga_crossover(parent1, parent2, top_n)
            ### Avoid Local Optima: Genetic mutation to avoid repetition and falling into local solutions
            child = ga_mutate(child, all_products, mutation_rate, top_n)
            new_pop.append(child)
            
        pop = new_pop
        
    return best_chrom, global_best, history


# ---- Quick Recommendation Helper ----
# A simple wrapper that calls ga_optimize with default settings.
# Used by the Store page to get recommendations without extra setup.
def get_recommendations(user_id, u_feat, p_feat, behavior):
    """Get a list of recommended product IDs for a given user."""
    best_items, score, history = ga_optimize(user_id, u_feat, p_feat, behavior, pop_size=20, generations=15)
    return best_items
