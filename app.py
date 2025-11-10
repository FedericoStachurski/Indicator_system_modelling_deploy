'''
Useful commands to run this app:
python3  -m venv streamlitEnv
source streamlitEnv/bin/activate
pip3 install -r requirements.txt
python3 -m streamlit run app.py


Useful commands to set up a git repository:
cd /Users/cris.hasan/Desktop/online_github_repositories/Indicator_system_modelling/
git init
git status
git add .
git commit -m "Minor changes to app.py"
git branch -M main 
git push -u origin main
'''
###############################################
import streamlit as st
from scipy import integrate
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
################################################
#set the default font for all figures
font_families = matplotlib.font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Computer Modern']
plt.rcParams['text.usetex'] = True
###############################################
# Functions
def simple_plot(x, y, xlabel="X", ylabel="Y", title="Simple Plot", label=None, save_as=None):
    plt.figure(figsize=(5, 3), dpi=150)
    plt.plot(x, y, label=label)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    if label:
        plt.legend()
    plt.tight_layout()
    if save_as:
        plt.savefig(save_as, format=save_as.split('.')[-1])
        print(f"Plot saved as '{save_as}'")
    
    st.pyplot(plt)  # Show the plot in Streamlit

def plot_multiple_xy(pairs, xlabel="X", ylabel="Y", title="Multiple Line Plot", scatter = False, labels=None, save_as=None):
    plt.figure(figsize=(5, 3), dpi=150)
    for i, (x, y) in enumerate(pairs):
        label = labels[i] if labels and i < len(labels) else None
        if scatter and i == 0:
            plt.plot(x, y, label=label)
            plt.scatter(x, y, label=None)
        else:
            plt.plot(x, y, label=label)

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    if labels:
        plt.legend(fontsize='small')
    plt.tight_layout()
    if save_as:
        plt.savefig(save_as, format=save_as.split('.')[-1])
        print(f"Plot saved as '{save_as}'")
    
    st.pyplot(plt) 

def plot_fill_between(pairs, xlabel="X", ylabel="Y", title="Fill Between Plot", labels=None, save_as=None):
    plt.figure(figsize=(5, 3), dpi=150)
    last_y = np.zeros_like(pairs[0][1])  # Initialize with zeros for first fill
    for i, (x, y) in enumerate(pairs):
        label = labels[i] if labels and i < len(labels) else None
        plt.fill_between(x, last_y, last_y + y, label=label, alpha=0.3) # bottom is last_y, top is last_y + y
        last_y += y  # Stack the next fill on top of current total  

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    if labels:
        plt.legend(loc='lower left', fontsize='small', ncol=2)  # Adjust legend for better visibility
    plt.tight_layout()
    if save_as:
        plt.savefig(save_as, format=save_as.split('.')[-1])
        print(f"Plot saved as '{save_as}'")

    st.pyplot(plt)  # Show the plot in Streamlit

def plot_bar_dict(time, dictionary, xlabel="Time", ylabel="Value", title="Bar Plot", labels=None, save_as=None):
    plt.figure(figsize=(5, 3), dpi=150)
    variables = list(dictionary.values())  # Extract the values from the dictionary
    bottom = np.zeros(len(time))  # Initialize bottom for stacking
    for i, values in enumerate(variables):
            label = labels[i] if labels and i < len(labels) else None
            plt.bar(time , values/1e6, bottom=bottom, label=label)
            bottom += values/1e6  # Update bottom for the next bar

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    if labels:
        plt.legend(fontsize='small',bbox_to_anchor=(1.01, 0.5), loc='center left', borderaxespad=1.5)
    plt.tight_layout()
    if save_as:
        plt.savefig(save_as, format=save_as.split('.')[-1])
        print(f"Plot saved as '{save_as}'")

    st.pyplot(plt)  # Show the plot in Streamlit

def plot_histogram_dict(data_dict, xlabel="Value", ylabel="Frequency", title="Histogram", bins=10, save_as=None):
    # Create a histogram where the x-axis represents the keys and the y-axis represents the values
    plt.figure(figsize=(5, 3), dpi=150)
    keys = list(data_dict.keys())
    values = list(data_dict.values())
    plt.bar(keys, values, alpha=0.7)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    if save_as:
        plt.savefig(save_as, format=save_as.split('.')[-1])
        print(f"Histogram saved as '{save_as}'")
    
    st.pyplot(plt)  # Show the plot in Streamlit

def plot_multiple_histogram_dict(data_dict_list, xlabel="Value", ylabel="Frequency", title="Multiple Histograms", bins=10, labels=None, save_as=None):
    plt.figure(figsize=(5, 3), dpi=150)
    for i, data_dict in enumerate(data_dict_list):
        keys = list(data_dict.keys())
        values = list(data_dict.values())
        plt.bar(keys, values, alpha=0.7, label=labels[i] if labels else None)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    if labels:
        plt.legend(loc='upper left', fontsize='small', ncol=1)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    if save_as:
        plt.savefig(save_as, format=save_as.split('.')[-1])
        print(f"Histogram saved as '{save_as}'")

    st.pyplot(plt)

def compute_yield_t_per_ha(food_production_dict, land_ha):
    # Function to compute yield estimates in tonnes per hectare
    total_prod = 0
    for item in food_production_dict:
        prod_t = food_production_dict[item]
        total_prod += prod_t
    
    yield_per_hectare = total_prod / land_ha
    return yield_per_hectare

def create_area_percentage_dict(food_production_dict, yield_t_per_ha, total_land_ha):
    # Function to create a dictionary for area percentage for each produce type
    area_percentage_dict = {}
    for item in food_production_dict:
        area_percentage = (food_production_dict[item] / yield_t_per_ha) / total_land_ha
        area_percentage_dict[item] = area_percentage
    return area_percentage_dict

def create_food_production_dict(yield_t_per_ha, dynamic_land_ha, area_percentage_dict):
    # Function to create a food production dictionary based on yield rate, dynamic land area, area percentage
    food_production_dict = {}
    for item in area_percentage_dict:
        food_production_dict[item] = yield_t_per_ha * dynamic_land_ha * area_percentage_dict[item]
    return food_production_dict 

def compute_total_calories(dynamic_food_production_dict, food_calories_per_tonne):
    # Function to compute the total calories in kilo calories for each category
    first_value = list(dynamic_food_production_dict.values())[0]
    total_calories = np.zeros_like(first_value)
    for item in dynamic_food_production_dict:
        prod_t = dynamic_food_production_dict[item]  # production in tonnes
        calories_per_tonne = food_calories_per_tonne[item]
        total_calories += prod_t * calories_per_tonne
    return total_calories

def compute_consumption_in_tonnes_dict(food_consumption_dict, dynamic_population):
    # Function to compute consumption dictionary for each commodity
    # Here we assume that food consumption per capita is constant over time, using the 2019 data as a reference
    consumption_per_capita = {}
    consumption_in_tonnes_dict = {}    
    for item in food_consumption_dict:
        consumption_per_capita[item] = food_consumption_dict[item] / dynamic_population[0]
        consumption_in_tonnes_dict[item] = consumption_per_capita[item] * dynamic_population

    return consumption_in_tonnes_dict

def compute_SSR_by_commodity_dict(dynamic_total_consumption_in_calories_dict, dynamic_all_food_prodction_dict):
    # Function to compute the Self-sufficiency ratio (SSR) for each commodity
    SSR_by_commodity_dict = {}
    for item in dynamic_all_food_prodction_dict:
        # We don't need the calories per tonne here since we are computing the SSR for each commodity
        # In other words, iff item by item, the following is ture: production_in_tonnes/consumption_in_tonnes = production_in_calories/consumption_in_calories
        production_in_tonnes = dynamic_all_food_prodction_dict[item]
        consumption_in_tonnes = dynamic_total_consumption_in_calories_dict[item]
        SSR_by_commodity_dict[item] = 100 * (production_in_tonnes / consumption_in_tonnes)
    return SSR_by_commodity_dict

def compute_agricultural_emissions(dynamic_food_production_dict, carbon_emissions_per_tonne):
    # Function to compute agricultural emissions in tonnes of CO₂ equivalent for each category
    first_value = list(dynamic_food_production_dict.values())[0]
    total_emissions = np.zeros_like(first_value)
    for item in dynamic_food_production_dict:
        prod_t = dynamic_food_production_dict[item]  # production in tonnes
        emissions_per_tonne = carbon_emissions_per_tonne[item]
        total_emissions += prod_t * emissions_per_tonne
    return total_emissions


def compute_dynamic_peatland_emissions(dynamic_restored_peatland_ha, carrying_capacity_restored_peatland, degraded_peatland_carbon_emissions_per_ha):
    # Function to compute peatland emissions in tonnes of CO₂ equivalent
    degraded_peatland_ha = carrying_capacity_restored_peatland - dynamic_restored_peatland_ha
    dynamic_peatland_emissions = degraded_peatland_ha * degraded_peatland_carbon_emissions_per_ha
    return dynamic_peatland_emissions

def compute_normalised_household_income_shares(share_dict):
    # Function to compute normalised household income shares
    total_income = sum(share_dict.values())
    normalised_shares = {}
    cumulative_income_shares = {}
    for item in share_dict:
        normalised_shares[item] = 100 * share_dict[item] / total_income
        cumulative_income_shares[item] = sum(normalised_shares.values())
    return normalised_shares, cumulative_income_shares

def compute_average_income(share_dict, population_size):
    # Calculate average income per week for each decile
    average_income = {}
    for item in share_dict:
        # 10 for deciles, 1e6 in million pounds, 52 weeks, 
        average_income[item] = 10 * 1e6 * share_dict[item] / (52 * population_size) 
    return average_income

def average_income_projection(average_income_dict_initial, wage_growth_rate):
    # Project average income into the future using a growth rate
    projected_income = {}
    for item in average_income_dict_initial:
        projected_income[item] = average_income_dict_initial[item] * (1 + 0.01 * (wage_growth_rate - parameters.initial_wage_index))
    return projected_income

def calculate_food_poverty_index(average_income_dict_initial, food_cost_per_capita, wage_growth_rate):
    # Food poverty index is the share of income spent on food for the lowest 20% earners
    projected_income = average_income_projection(average_income_dict_initial, wage_growth_rate)
    average_income_in_lowest_20 = np.mean([projected_income["decile_1"], projected_income["decile_2"]])
    food_poverty_index = 100 * food_cost_per_capita / average_income_in_lowest_20
    return food_poverty_index

def food_poverty_projection(average_income_dict_initial, food_cost_per_capita, wage_growth_rate):
    # Project the food poverty index into the future using a wage growth rate array and food cost arrays
    projected_food_poverty_index_array = []
    for i in range(len(food_cost_per_capita)):
        projected_food_poverty_index = calculate_food_poverty_index(average_income_dict_initial, food_cost_per_capita[i], wage_growth_rate[i])
        projected_food_poverty_index_array.append(projected_food_poverty_index)
    return projected_food_poverty_index_array

def calculate_gini_index(cumulative_income_shares):
    # Function to calculate the Gini index from normalised household income shares
    N = len(cumulative_income_shares)
    sorted_shares = np.array(sorted(cumulative_income_shares.values())) # Just to ensure the shares are sorted
    delta_x = 1 / N
    Lorenz_curve_integral = np.sum(0.01*sorted_shares* delta_x) # Multiply by 0.01 to convert to rescale to [0,1]
    equality_line_integral = 1/2  # Area under the equality line
    A = equality_line_integral - Lorenz_curve_integral
    B = Lorenz_curve_integral
    gini_index = A / (A + B)
    return gini_index

def approximate_timeseries_for_dudt(u, dt=1):
    # Approximate the time series for dudt using finite differences.
    du_dt = np.zeros_like(u)
    du_dt[0] = (u[1] - u[0]) / dt  # Forward difference for the first element (1st order)
    du_dt[-1] = (u[-1] - u[-2]) / dt  # Backward difference for the last element (1st order)
    for i in range(1, len(u)-1):
        du_dt[i] = (u[i+1] - u[i-1]) / (2*dt)  # Central difference for interior points (2nd order)
    return du_dt

def food_cost_rhs_function(x, a, b, c):
    x_1, x_2, x_3 = x  # Unpack the input tuple
    # x_1, x_2, x_3 represent, year-on-year inflation rate, SSR, and food cost, respectively
    # The factor of 0.01 is to ensure that x_1 and x_2 are of the same order of magnitude
    return (a * 0.01 * x_1 + b * x_2) * x_3 + c

def curve_fit_for_food_cost_dudt(y, x_1, x_2, x_3, p0=[1, -1, 0]):
    # Function to fit a curve to the right-hand side of the ODEs
    # y is the dependent variable (dudt), and x_i are the independent variables
    # p0 is the initial guess for the parameters
    params, _ = curve_fit(food_cost_rhs_function, (x_1, x_2, x_3), y, p0=p0)
    return params

###############################################
# Define the right-hand side functions for the ODEs
def rhs_animal_land_ha(A, alpha, K, mu):
    rhs = alpha * A * (1 - A/K) - mu * A
    return rhs

def rhs_nonanimal_land_ha(N, A, beta, c, mu):
    rhs = beta * N * (1 - N/c) + mu * A
    return rhs

def rhs_population(population, birth_rate, death_rate, net_migration_rate):
    rhs = (birth_rate/1000 - death_rate/1000) * population + net_migration_rate
    return rhs

def rhs_inflation_index(inflation_index, linear_inflation_rate, exponential_inflation_rate, linear=False):
    # Source:https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7bt/mm23
    # We choose CPI, but we may opt for CPIH instead
    # 100 is the base year (2015)
    if linear:
        rhs = linear_inflation_rate
    else:
        rhs = exponential_inflation_rate * inflation_index
    return rhs

def rhs_food_cost(inflation_index, SSR, food_cost, food_cost_parameters):
    rhs = food_cost_rhs_function((inflation_index, SSR, food_cost), *food_cost_parameters)
    return rhs

def rhs_wage_growth(exponential_wage_growth_rate, wage_index):
    rhs = exponential_wage_growth_rate * wage_index
    return rhs

def rhs_woodlands_and_forest_land_ha(A, alpha, K):
    rhs = alpha * A * (1 - A/K)
    return rhs

def rhs_restored_peatland_ha(A, alpha, K, d):
    # A is the area of restored peatland, K is the carrying capacity, d is the degradation rate
    rhs = alpha * (K-A) - d * A
    return rhs

def all_rhs(t, u):
    # Function to compute the right-hand side of the system of ODEs
    u_animal_land_ha = u[0]
    u_nonanimal_land_ha = u[1]
    u_population = u[2]
    u_inflation_index = u[3]
    u_food_cost = u[4]
    u_wage_index = u[5]
    u_woodlands_and_forest_land_ha = u[6]
    u_restored_peatland_ha = u[7]
    dudt_animal_land_ha = rhs_animal_land_ha(u_animal_land_ha, parameters.animal_land_growth_rate, parameters.carrying_capacity_animal, parameters.conversion_rate_animal_to_nonanimal_land)
    dudt_nonanimal_land_ha = rhs_nonanimal_land_ha(u_nonanimal_land_ha, u_animal_land_ha, parameters.nonanimal_land_growth_rate, parameters.carrying_capacity_nonanimal, parameters.conversion_rate_animal_to_nonanimal_land)
    dudt_population = rhs_population(u_population, parameters.birth_rate, parameters.death_rate, parameters.net_migration_rate)
    dudt_inflation_index = rhs_inflation_index(u_inflation_index, parameters.linear_inflation_rate, parameters.exponential_inflation_rate, linear=parameters.linear_inflation)
    dudt_food_cost = rhs_food_cost(u_inflation_index, parameters.SSR_constant, u_food_cost, food_cost_parameters)
    dudt_wage_growth = rhs_wage_growth(parameters.exponential_wage_growth_rate, u_wage_index)
    dudt_woodlands_and_forest_land_ha = rhs_woodlands_and_forest_land_ha(u_woodlands_and_forest_land_ha, parameters.woodland_growth_rate, parameters.carrying_capacity_woodland)
    dudt_restored_peatland_ha = rhs_restored_peatland_ha(u_restored_peatland_ha, parameters.peatland_restoration_rate, parameters.carrying_capacity_restored_peatland, parameters.degradation_rate_restored_peatland)
    return [dudt_animal_land_ha, dudt_nonanimal_land_ha, dudt_population, dudt_inflation_index, dudt_food_cost, dudt_wage_growth, dudt_woodlands_and_forest_land_ha, dudt_restored_peatland_ha]

###############################################
#Dictionaries
animal_food_production_dict = {
    # Food commodity production data in Scotland. This is a crude estimation from the graph. 
    # Source: https://sefari.scot/research/assessing-scotland%E2%80%99s-self-sufficiency-of-major-food-commodities
    # Estimated production in tonnes (not thousand tonnes) per year in 2019.
    # Crude estimates based on the graph (using PDF Preview), not exact figures.
    "Dairy": 42/64 * 2 * 1_000_000,
    "Eggs": 56/64 * 2 * 1_000_000,
    "Pork": 0.5/64 * 2 * 1_000_000,
    "Poultry": 4/64 * 2 * 1_000_000,
    "Beef": 5/64 * 2 * 1_000_000,
    "Lamb": 1/64 * 2 * 1_000_000,
}

nonanimal_food_production_dict = {
    # Food commodity production data in Scotland. This is a crude estimation from the graph. 
    # Source: https://sefari.scot/research/assessing-scotland%E2%80%99s-self-sufficiency-of-major-food-commodities
    # Estimated production in tonnes per year in 2019.
    "Barley": 63/64 * 2 * 1_000_000,
    "Potatoes": 38/64 * 2 * 1_000_000,
    "Oats": 6/64 * 2 * 1_000_000,
    "Wheat": 30/64 * 2 * 1_000_000,
}

food_calories_per_tonne = {
    # Source: LLM estimates based on average caloric content per tonne of each commodity
    # Measured in kcal per tonne
    "Barley": 3_400_000,   # Dry grain, high carbohydrate
    "Potatoes": 750_000,   # ~80% water
    "Oats": 3_500_000,     # Similar to barley
    "Wheat": 3_400_000,    # Dry grain
    "Dairy": 650_000,      # Whole milk (~87% water)
    "Eggs": 1_600_000,     # Includes shell weight
    "Pork": 2_200_000,     # Raw, medium fat content
    "Poultry": 2_000_000,  # Chicken, raw
    "Beef": 1_800_000,     # Raw, varies by cut
    "Lamb": 2_000_000,     # Similar to beef
}

carbon_emissions_per_tonne = {
    # Source: (LLM) Estimates based on meta-analyses of LCA studies (Poore & Nemecek 2018, FAO, etc.)
    # Measured in tonne CO₂eq per tonne of product
    # Note these estimates are inflated and need to be reviewed
    "Barley": 0.3,      # Cereal crops generally low-emission
    "Potatoes": 0.15,     # Very efficient crop per tonne
    "Oats": 0.35,         # Similar to barley
    "Wheat": 0.4,        # Slightly higher than barley
    "Dairy": 2.5,      # Milk (includes methane from cattle)
    "Eggs": 2.0,       # Chicken farming emissions
    "Pork": 4.8,       # Pig rearing (feed + manure management)
    "Poultry": 3.5,    # Chicken (better feed conversion than pork/beef)
    "Beef": 15.0,      # Beef from beef herds (highest emitter)
    "Lamb": 20.0,      # Even higher than beef (lower yields per animal)
}

total_land_area_by_type = {
    # Estimated land areas in Scotland for different types of agriculture
    "cereals_oilseeds_potatoes": 500_000,  # ha
    "grassland_rough_grazing": 4_400_000   # ha
}

yield_per_hectare = {
    # Yield estimates (tonnes per hectare)
    # Source: LLM estimates based on average yields for each commodity
    # Crops (dry weight unless noted)
    "Barley": 6.5,       # UK average (range: 5-8 t/ha)
    "Potatoes": 45.0,    # Fresh weight, high-yield UK varieties
    "Oats": 5.5,         # Similar to barley
    "Wheat": 7.5,        # UK average (range: 6-9 t/ha)
    # Animal products (live weight or equivalent)
    "Dairy": 1.2,        # Milk solids (~10,000 L/ha/yr ≈ 1.2 t solids)
    "Eggs": 0.15,        # ~150 kg/ha/yr (industrial poultry)
    "Pork": 1.8,         # Carcass weight (intensive systems)
    "Poultry": 1.5,      # Broilers, carcass weight
    "Beef": 0.6,         # Carcass weight (grass-fed systems)
    "Lamb": 0.4,         # Carcass weight (grass-fed)
}

alternative_yield_per_hectare = {
    # Alternative yield estimates based on total production and land area
    "Barley": 3,       # t/ha
    "Potatoes": 30,    # t/ha
    "Oats": 3,         # t/ha
    "Wheat": 4,        # t/ha
    "Dairy": 2,        # t/ha equivalent (very rough estimate)
    "Eggs": 1,         # t/ha equivalent
    "Pork": 0.5,       # t/ha equivalent
    "Poultry": 0.5,    # t/ha equivalent
    "Beef": 0.1,       # t/ha equivalent
    "Lamb": 0.1        # t/ha equivalent
}

food_consumption_dict = {
    # Source: https://sefari.scot/research/assessing-scotland%E2%80%99s-self-sufficiency-of-major-food-commodities
    # Estimated production in tonnes (not thousand tonnes) per year in 2019.
    # Using the SSR table. The graph must be wrong!
    "Dairy": 42/64 * 2 * 1_000_000 / 1.118,
    "Eggs": 56/64 * 2 * 1_000_000 / 1.018,
    "Pork": 0.5/64 * 2 * 1_000_000 / 0.263,
    "Poultry": 4/64 * 2 * 1_000_000 / 0.795,
    "Beef": 5/64 * 2 * 1_000_000 / 1.463,
    "Lamb": 1/64 * 2 * 1_000_000 / 0.999,
    "Barley": 63/64 * 2 * 1_000_000 / 1.661,
    "Potatoes":29/52 * 1_000_000 / 1.278, 
    "Oats":6/64 * 2 * 1_000_000 / 2.226, 
    "Wheat": 25/52 * 1_000_000 / 1.075,
}

BHC_household_income_shares_dict = {
    # (Before housing cost) Annual household income shares in £ million in 2019
    # Source: Single-year estimates, sheet 11, https://data.gov.scot/poverty/2024/download.html
    "decile_1": 6006,
    "decile_2": 9937,
    "decile_3": 12275,
    "decile_4": 14575,
    "decile_5": 16742,
    "decile_6": 19243,
    "decile_7": 21741,
    "decile_8": 24716,
    "decile_9": 28947,
    "decile_10": 48371
}

AHC_household_income_shares_dict = {
    # (After housing cost) Annual household income shares in £ million in 2019
    # Source: Single-year estimates, sheet 11, https://data.gov.scot/poverty/2024/download.html
    "decile_1": 3888,
    "decile_2": 7804,
    "decile_3": 10651,
    "decile_4": 12878,
    "decile_5": 15375,
    "decile_6": 17451,
    "decile_7": 20007,
    "decile_8": 22779,
    "decile_9": 26630,
    "decile_10": 46897
}

###############################################
# Time series
# Ideally, this data will imported from an external source, such as a CSV file or a database.
food_expenditure_series = {
    # Source: Figure 3 data from  https://www.ons.gov.uk/economy/inflationandpriceindices/bulletins/onshouseholdexpendituredatainsightsintotheeffectsofcostsoflivingpressures/4december2023
    # Total food expenditure in million pounds (nominal) in the UK (2005-2022)
    # Aggregated over 4 quarters for each year. Note: need to sum over Column C which corresponds to the Current Price (nominal)
    # Remove the 2005 data point since the jump from 2005 to 2006 is an outlier
    str(y): p for y, p in zip(range(2006, 2023), [
        70234,73367,77885,80070,81424,87431,89867,93003,94365,92445,98106,103448,107488,109531,116529,117950,124039
        ])}

UK_population_series = {
    # Source: https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/timeseries/ukpop/pop
    # UK population estimates (2006-2022)
    str(y): p for y, p in zip(range(2006, 2023), [
    60827100, 61319100, 61823800, 62260500, 62759500, 63285100, 63710800, 64138700, 64619500, 65088100, 65607100, 65966000, 66288900, 66630700, 66744100, 66983500, 67602800
])}

food_cost_per_capita_series = {
    # Calculate food expenditure per capita in pounds per week
    year: (1e6*food_expenditure_series[year] / UK_population_series[year]) / 52
    for year in food_expenditure_series
}

inflation_index_series = {
    # Source:https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7bt/mm23
    # 100 is the base year (2015)
    # We choose CPI, but we may opt specifically for food inflation index instead
    str(y): p for y, p in zip(range(2006, 2023), [
    79.9, 81.8, 84.7, 86.6, 89.4, 93.4, 96.1, 98.5, 100.0, 100.0, 100.7, 103.4, 105.9, 107.8, 108.7, 111.6, 121.7
])}

SSR_series = {
    # Here, we assume that SSR has been constant over the years, using the 2019 data as a reference
    # We do this because we have a time series for SSR in tonnes but not in calories; and calculate SSR in our model in calories. 
    # 1.5% SSR for all years
    str(y): p for y, p in zip(range(2006, 2023), [
        1.5 for _ in range(2006, 2023)
])}

###############################################
# I could remove all time series and only use the numpy arrays in the future 
food_cost_per_capita_array = np.array(list(food_cost_per_capita_series.values()))
inflation_index_array = np.array(list(inflation_index_series.values()))
SSR_array = np.array(list(SSR_series.values()))

y_dudt_food_cost_array = approximate_timeseries_for_dudt(food_cost_per_capita_array, dt=1)
dudt_inflation_index_array = approximate_timeseries_for_dudt(inflation_index_array, dt=1)
###############################################
# Best-value values for regression parameters
food_cost_parameters = curve_fit_for_food_cost_dudt(y_dudt_food_cost_array, inflation_index_array, SSR_array, food_cost_per_capita_array)
#print(f"Fitted parameters for food cost dudt: {food_cost_parameters}")
# Fitted functions
yhat_dudt_food_cost_array = food_cost_rhs_function((inflation_index_array, SSR_array, food_cost_per_capita_array), *food_cost_parameters)
# Compute Mean Squared Error (MSE)
mse_food_cost = np.mean((y_dudt_food_cost_array - yhat_dudt_food_cost_array) ** 2)
# Compute Normalized Root Mean Squared Error (NRMSE)
nrmse_food_cost = np.sqrt(mse_food_cost) / np.mean(y_dudt_food_cost_array)
###############################################
class Parameters:
    # Define a class to hold the parameters
    def __init__(self):
        self.initial_year = 2019  # Initial year for the model
        self.final_year = 2050    # Final year for the model
        self.initial_animal_land_ha = total_land_area_by_type["grassland_rough_grazing"]
        self.initial_nonanimal_land_ha = total_land_area_by_type["cereals_oilseeds_potatoes"]
        self.initial_population = 5_400_000  # Initial population of Scotland in 2019
        self.initial_inflation_index = 106.3  # Initial inflation index (2019 = 106.3)
        self.initial_food_cost = food_cost_per_capita_series["2019"] # Initial food cost per capita in pounds per week
        self.initial_wage_index = 106.3  # Initial wage growth index (2019 = 106.3)
        self.initial_woodlands_and_forest_land_ha = 1_500_000  # (roughly 19.2% of Scotland total land) Initial woodland and forest land area in hectares
        self.initial_restored_peatland_ha = 360_000 # ha (80% of the total peatland area)
        self.conversion_rate_animal_to_nonanimal_land = 1/1000  # Conversion rate from animal to non-animal land
        self.carrying_capacity_animal = 5_000_000  # Carrying capacity for animal land in hectares (for zero conversion rate)
        self.carrying_capacity_nonanimal = 2_000_000  # Carrying capacity for non-animal land in hectares (for zero conversion rate)
        self.carrying_capacity_woodland = 2_200_000  # Carrying capacity for woodland and forest land in hectares
        self.carrying_capacity_restored_peatland = 1_800_000 # (ha) This figure varies among different sources (20 to 23% of Scotland land)
        self.peatland_restoration_rate = 0.007 # Restoration rate for degraded peatland: ratio between annual rate (8,000 ha) and total degraded peatland (total peatland - restored peatland)
        self.degradation_rate_restored_peatland = 0.001  # (depends on climate change scenarios) Degradation rate for restored peatland
        self.degraded_peatland_carbon_emissions_per_ha = 5.0  # (tCO₂eq/ha/yr) Tonnes of CO₂ equivalent per hectare per year from degraded peatland
        self.peatland_average_storage_per_ha_initial = 1_370  # (tC/ha in 2019) Tonnes of carbon per hectare stored in peatland
        self.peatland_sequestration_rate = 1.23  # (tCO₂eq/ha/yr) Tonnes of carbon per hectare per year sequestered (captured) in restored peatland
        self.woodland_average_storage_per_ha_initial = 1333  # (tC/ha in 2019) Tonnes of carbon per hectare stored in woodland
        self.woodland_sequestration_rate = 4.87  # (tCO₂eq/ha/yr) Tonnes of carbon per hectare per year sequestered (captured) in restored woodland
        self.animal_land_growth_rate = 1/1000  # Growth rate for animal land (before intervention)
        self.nonanimal_land_growth_rate = 1/1000   # Growth rate for non-animal land (before intervention)
        self.woodland_growth_rate = 0.01  # Growth rate for woodland and forest land (roughly 15,000 hectares per year in the first few years)
        self.birth_rate = 7.46  # Birth rate per 1000 people
        self.death_rate = 8.66  # Death rate per 1000 people
        self.net_migration_rate = 28_000  # Net migration rate per year
        self.linear_inflation = False  # Use linear inflation model (True) or exponential (False)
        self.linear_inflation_rate = (106.3-48.4) / (2019-1988)  # Linear rate of inflation from 1988 to 2019
        self.exponential_inflation_rate = (1 / (2019 - 1949)) * np.log(106.3-48.4) # Exponential rate of inflation from 1949 to 2019
        self.SSR_constant = 1.5  # Assuming self-sufficiency ratio (SSR) is constant for the model
        self.exponential_wage_growth_rate = 0.02  # Exponential wage growth rate (2% per year)

# Create instance
parameters = Parameters()
###############################################
# Set the title of the app
st.title("Indicator system modelling: Proof of Concept")
st.subheader(f"Key parameters")
parameters.birth_rate = st.slider("Select a value for annual birth rate", min_value=2.0, max_value=20.0, value=parameters.birth_rate, step=0.01)
st.write(f"You selected a birth rate of: {parameters.birth_rate} per 1000 people per year.")
parameters.death_rate = st.slider("Select a value for annual mortality rate", min_value=2.0, max_value=20.0, value=parameters.death_rate, step=0.01)
st.write(f"You selected a mortality rate of: {parameters.death_rate} per 1000 people per year.")
parameters.exponential_inflation_rate = st.slider("Select a value for the year-on-year (exponential) inflation rate", min_value=0.0, max_value=0.1, value=parameters.exponential_inflation_rate, step=0.0001)
st.write(f"You selected an exponential inflation rate of: {parameters.exponential_inflation_rate} per year.")
parameters.exponential_wage_growth_rate = st.slider("Select a value for the year-on-year (exponential) wage growth rate", min_value=0.0, max_value=0.1, value=parameters.exponential_wage_growth_rate, step=0.0001)
st.write(f"You selected an exponential wage growth rate of: {parameters.exponential_wage_growth_rate} per year.")
parameters.conversion_rate_animal_to_nonanimal_land = st.slider("Select a value for the coversion rate from animal to non-animal farm land", min_value=0.0, max_value=0.01, value=parameters.conversion_rate_animal_to_nonanimal_land, step=0.0001)
st.write(f"You selected a conversion rate of: {parameters.conversion_rate_animal_to_nonanimal_land*100} \% per year.")
parameters.degradation_rate_restored_peatland = st.slider("Select a value for the degradation rate of restored peatland", min_value=0.0, max_value=0.1, value=parameters.degradation_rate_restored_peatland, step=0.0001)
st.write(f"You selected a degradation rate of {parameters.degradation_rate_restored_peatland} per year.")
parameters.woodland_growth_rate = st.slider("Select a value for the annual woodland and forest land (logistic) growth rate", min_value=0.0, max_value=0.1, value=parameters.woodland_growth_rate, step=0.001)
st.write(f"You selected a woodland growth (afforestation) rate of: {parameters.woodland_growth_rate*100} \% per year.")
# Uncertainty parameters
st.subheader(f"Uncertainty parameters")
parameters.initial_restored_peatland_ha = st.slider("Select a value for initial restored peatland area", min_value=200_000, max_value=600_000, value=parameters.initial_restored_peatland_ha, step=1000)
st.write(f"You selected an initial restored peatland area of: {parameters.initial_restored_peatland_ha} hectares.")
parameters.peatland_restoration_rate = st.slider("Select a value for peatland restoration rate", min_value=0.0, max_value=0.05, value=parameters.peatland_restoration_rate, step=0.0001)
st.write(f"You selected a (year-on-year) peatland restoration rate of {parameters.peatland_restoration_rate*100}% of degraded peatland per year.")
parameters.degraded_peatland_carbon_emissions_per_ha = st.slider("Select a value for degraded peatland carbon emissions per hectare", min_value=1.0, max_value=10.0, value=parameters.degraded_peatland_carbon_emissions_per_ha, step=0.01)
st.write(f"You selected a degraded peatland carbon emissions of {parameters.degraded_peatland_carbon_emissions_per_ha} tCO₂eq/ha/yr.")
parameters.peatland_sequestration_rate = st.slider("Select a value for peatland sequestration rate", min_value=0.1, max_value=10.0, value=parameters.peatland_sequestration_rate, step=0.001)
st.write(f"You selected a (year-on-year) peatland sequestration rate of {parameters.peatland_sequestration_rate} tCO₂eq/ha/yr.")
parameters.woodland_sequestration_rate = st.slider("Select a value for woodland sequestration rate", min_value=0.1, max_value=10.0, value=parameters.woodland_sequestration_rate, step=0.01)
st.write(f"You selected a (year-on-year) woodland sequestration rate of {parameters.woodland_sequestration_rate} tCO₂eq/ha/yr.")
parameters.carrying_capacity_woodland = st.slider("Select a value for initial woodland carrying capacity", min_value=1800000, max_value=2800000, value=parameters.carrying_capacity_woodland, step=100000)
st.write(f"You selected an initial woodland carrying capacity of: {parameters.carrying_capacity_woodland} tonnes of carbon per hectare.")
parameters.woodland_average_storage_per_ha_initial = st.slider("Select a value for woodland average carbon storage per hectare", min_value=1000, max_value=1600, value=parameters.woodland_average_storage_per_ha_initial, step=100)
st.write(f"You selected an woodland average carbon storage of: {parameters.woodland_average_storage_per_ha_initial} tonnes of carbon per hectare.")

sol = integrate.solve_ivp(
    all_rhs, 
    [parameters.initial_year, parameters.final_year], 
    [parameters.initial_animal_land_ha, parameters.initial_nonanimal_land_ha, parameters.initial_population, parameters.initial_inflation_index, parameters.initial_food_cost, parameters.initial_wage_index, parameters.initial_woodlands_and_forest_land_ha, parameters.initial_restored_peatland_ha],
    #args=(other_arguments),
    t_eval=np.arange(parameters.initial_year, parameters.final_year + 1, 1),
    method='RK45'
)

dynamic_animal_land_ha = sol.y[0]
dynamic_nonanimal_land_ha = sol.y[1]
dynamic_population = sol.y[2] 
dynamic_inflation_index = sol.y[3]
dynamic_food_cost = sol.y[4]
dynamic_wage_growth_index = sol.y[5]
dynamic_woodlands_and_forest_land_ha = sol.y[6]
dynamic_restored_peatland_ha = sol.y[7]
###############################################
# Estimate total yield (in tonnes per hectare) for each land category
animal_yield_t_per_ha = compute_yield_t_per_ha(animal_food_production_dict, parameters.initial_animal_land_ha)
nonanimal_yield_t_per_ha = compute_yield_t_per_ha(nonanimal_food_production_dict, parameters.initial_nonanimal_land_ha)
# Create a dictionary for area percentage for each produce type
animal_area_percentage_dict = create_area_percentage_dict(animal_food_production_dict, animal_yield_t_per_ha, parameters.initial_animal_land_ha)
nonanimal_area_percentage_dict = create_area_percentage_dict(nonanimal_food_production_dict, nonanimal_yield_t_per_ha, parameters.initial_nonanimal_land_ha)
###############################################
# Derived dynamic variables
# Dynamic food production by commodity (dictionaries)
dynamic_animal_food_production_dict = create_food_production_dict(animal_yield_t_per_ha, dynamic_animal_land_ha, animal_area_percentage_dict)
dynamic_nonanimal_food_production_dict = create_food_production_dict(nonanimal_yield_t_per_ha, dynamic_nonanimal_land_ha, nonanimal_area_percentage_dict)
combined_food_production_dict = {**dynamic_animal_food_production_dict, **dynamic_nonanimal_food_production_dict} # Double asterisk operator to unpack the two dictionaries before merging them
new_order = ["Lamb", "Beef", "Poultry", "Pork", "Eggs", "Dairy", "Wheat", "Oats", "Potatoes", "Barley"]  # Define your desired order
dynamic_all_food_prodction_dict = {k: combined_food_production_dict[k] for k in new_order}
# Total food production (in tonnes)
dynamic_animal_total_food_production = sum(dynamic_animal_food_production_dict.values())
dynamic_nonanimal_total_food_production = sum(dynamic_nonanimal_food_production_dict.values())
# Calculate the total food production (in kilo calories)
dynamic_animal_total_calories = compute_total_calories(dynamic_animal_food_production_dict, food_calories_per_tonne)
dynamic_nonanimal_total_calories = compute_total_calories(dynamic_nonanimal_food_production_dict, food_calories_per_tonne)
# Calculate food consumption in tonnes
dynamic_consumption_in_tonnes_dict = compute_consumption_in_tonnes_dict(food_consumption_dict, dynamic_population)
dynamic_total_consumption = np.sum(list(dynamic_consumption_in_tonnes_dict.values()), axis=0)
# Calculate food consumption in calories
dynamic_total_consumption_calories = compute_total_calories(dynamic_consumption_in_tonnes_dict, food_calories_per_tonne)
# Calculate Self-sufficiency ratio (SSR)
dynamic_self_sufficiency_ratio = 100 * (dynamic_animal_total_calories + dynamic_nonanimal_total_calories) / dynamic_total_consumption_calories
# Self-sufficiency ratio by commodity
dynamic_self_sufficiency_ratio_by_commodity = compute_SSR_by_commodity_dict(dynamic_consumption_in_tonnes_dict, dynamic_all_food_prodction_dict)
# Calculate the total emissions (in tonnes of CO₂ equivalent)
dynamic_animal_total_emissions = compute_agricultural_emissions(dynamic_animal_food_production_dict, carbon_emissions_per_tonne)
dynamic_nonanimal_total_emissions = compute_agricultural_emissions(dynamic_nonanimal_food_production_dict, carbon_emissions_per_tonne)
# Calculate normalised household income shares
BHC_normalised_household_income_shares_dict, BHC_cumulative_income_shares = compute_normalised_household_income_shares(BHC_household_income_shares_dict)
gini_index = calculate_gini_index(BHC_cumulative_income_shares)
#print(gini_index)
# Calculate average income per person per week for each decile
average_income_dict_initial = compute_average_income(BHC_household_income_shares_dict, dynamic_population[0])
average_income_dict_final = average_income_projection(average_income_dict_initial, dynamic_wage_growth_index[-1])
# Calculate projected food poverty index for each year
projected_food_poverty_index_array = food_poverty_projection(average_income_dict_initial, dynamic_food_cost, dynamic_wage_growth_index)
# Calculate projected peatland emissions
projected_peatland_emissions = compute_dynamic_peatland_emissions(dynamic_restored_peatland_ha, parameters.carrying_capacity_restored_peatland, parameters.degraded_peatland_carbon_emissions_per_ha)
# Calculate peatland annual carbon sequestration
peatland_annual_carbon_sequestration = dynamic_restored_peatland_ha * parameters.peatland_sequestration_rate
# Calculate initial carbon stock (2019)
peatland_stock_initial = parameters.carrying_capacity_restored_peatland * parameters.peatland_average_storage_per_ha_initial
woodland_stock_initial = dynamic_woodlands_and_forest_land_ha * parameters.woodland_average_storage_per_ha_initial
# Calculate net emissions from woodland (net emissions = - sequestration)
woodland_net_emissions = dynamic_woodlands_and_forest_land_ha * (-parameters.woodland_sequestration_rate)
# Calculate carbon stock
projected_peatland_carbon_stock = peatland_stock_initial +  peatland_annual_carbon_sequestration - projected_peatland_emissions
projected_woodland_carbon_stock = woodland_stock_initial - woodland_net_emissions
###############################################
# Plot the results
# Plot population over time
st.subheader("Population Over Time")
simple_plot(
    x=sol.t, y=dynamic_population/1e6,
    xlabel="Year", ylabel="Population (Millions)",
    title="Population Over Time",
    label="Population",
    #save_as="population_over_time.pdf"
)

# Plot land area over time
st.subheader("Land Area Over Time")
plot_fill_between(
    pairs=[(sol.t, dynamic_animal_land_ha/1e6), (sol.t, dynamic_nonanimal_land_ha/1e6)],
    labels=["Animal Land", "Non-Animal Land"],
    xlabel="Year", ylabel="Million Hectares",
    title="Land Area Over Time",
    #save_as="land_area_over_time.pdf"
)

# Plot food production over time in mass
st.subheader("Food Production (mass) by Category")
plot_fill_between(
    pairs=[(sol.t, dynamic_animal_total_food_production/1e6), 
           (sol.t, dynamic_nonanimal_total_food_production/1e6)],
    labels=["Animal Food Production", "Non-Animal Food Production"],
    xlabel="Year", ylabel="Million Tonnes",
    title="Food Production in Tonnes",
    #save_as="food_production_mass.pdf"
)   

# Plot food production by category over time
st.subheader("Food Production by Subcategory Over Time")
plot_bar_dict(
    time=sol.t,
    dictionary=dynamic_all_food_prodction_dict,
    xlabel="Year", ylabel="Million Tonnes",
    title="Animal Food Production by Category",
    labels=list(dynamic_all_food_prodction_dict.keys()),
    #save_as="animal_food_production_by_category.pdf"
)

# Plot food production over time in calories
st.subheader("Food Production (Energy Content)")
plot_multiple_xy(
    pairs=[(sol.t, (dynamic_animal_total_calories/dynamic_population)/365.25), 
           (sol.t, (dynamic_nonanimal_total_calories/dynamic_population)/365.25)],
    labels=["Animal Food Production", "Non-Animal Food Production"],
    xlabel="Year", ylabel="Kcal per capita per day",
    title="Food Production in Calories",
    #save_as="food_production_calories.pdf"
)

# Plot food consumption vs production over time
st.subheader("Food Consumption vs Production Over Time")
plot_fill_between(
    pairs=[(sol.t, dynamic_animal_total_calories + dynamic_nonanimal_total_calories),
              (sol.t, dynamic_total_consumption_calories)],
    labels=["Total Food Production", "Total Food Consumption"],
    xlabel="Year", ylabel="Kcal",
    title="Food Consumption vs Production Over Time",
           )

# Plot Self-sufficiency ratio over time
st.subheader("Self-Sufficiency Ratio Over Time")
simple_plot(
    x=sol.t, y=dynamic_self_sufficiency_ratio,
    xlabel="Year", ylabel="Self-Sufficiency Ratio (\%)",
    title="Self-Sufficiency Ratio Over Time",
    label="Self-Sufficiency Ratio (SSR)",
    #save_as="self_sufficiency_ratio_over_time.pdf"
)

# Plot Self-sufficiency ratio by commodity
st.subheader("Self-Sufficiency Ratio by Commodity Over Time")
plot_multiple_xy(
    pairs=[(sol.t, dynamic_self_sufficiency_ratio_by_commodity[commodity]) for commodity in dynamic_self_sufficiency_ratio_by_commodity],
    xlabel="Year", ylabel="Self-Sufficiency Ratio (\%)",
    title="Self-Sufficiency Ratio by Commodity",
    labels=list(dynamic_self_sufficiency_ratio_by_commodity.keys()),
    #save_as="self_sufficiency_ratio_by_commodity.pdf"
)

# Plot woodlands and forest land over time
st.subheader("Woodlands and Forest Land Over Time")
plot_fill_between(
    pairs=[(sol.t, dynamic_woodlands_and_forest_land_ha/1e6)],
    labels=["Woodlands and Forest Land"],
    xlabel="Year", ylabel="Million ha",
    title="Woodlands and Forest Land Over Time",
)

# Plot restored peatland over time
st.subheader("Restored Peatland Over Time")
plot_fill_between(
    pairs=[(sol.t, dynamic_restored_peatland_ha/1e6),
           (sol.t, (parameters.carrying_capacity_restored_peatland - dynamic_restored_peatland_ha)/1e6)],
    labels=["Restored Peatland", "Degraded Peatland"],
    xlabel="Year", ylabel="Million ha",
    title="Restored Peatland Over Time",
)

# Plot carbon stock in peatland
st.subheader("Projected Carbon Stock in Peatland Over Time")
plot_fill_between(
    pairs=[(sol.t, projected_peatland_carbon_stock/1e6)],
    labels=["Projected Carbon Stock in Peatland"],
    xlabel="Year", ylabel="Million tC",
    title="Projected Carbon Stock in Peatland Over Time",
)
# Plot carbon stock in woodland
st.subheader("Projected Carbon Stock in Woodland Over Time")
plot_fill_between(
    pairs=[(sol.t, projected_woodland_carbon_stock/1e6)],
    labels=["Projected Carbon Stock in Woodland"],
    xlabel="Year", ylabel="Million tC",
    title="Projected Carbon Stock in Woodland Over Time",
)

# Plot Agricultural emissions over time
st.subheader("Agricultural Emissions Over Time")
plot_fill_between(
    pairs=[(sol.t, dynamic_animal_total_emissions/1e6), 
           (sol.t, dynamic_nonanimal_total_emissions/1e6)],
    labels=["Animal Products", "Non-Animal Products"],
    xlabel="Year", ylabel="Million tCO$_2$eq",
    title="Agricultural Emissions Over Time",
    #save_as="emissions_over_time.pdf"
)

# Plot agricultural emissions per capita over time
st.subheader("Agricultural Emissions per Capita Over Time")
plot_fill_between(
    pairs=[(sol.t, dynamic_animal_total_emissions/dynamic_population), 
           (sol.t, dynamic_nonanimal_total_emissions/dynamic_population)],
    labels=["Animal Products", "Non-Animal Products"],
    xlabel="Year", ylabel="tCO$_2$eq/capita",
    title="Agricultural Emissions per Capita Over Time",
    #save_as="emissions_over_time.pdf"
)

# Plot Annual Net Peatland Emissions Over Time 
st.subheader("Annual Net Emissions from Peatland")
plot_fill_between(
    pairs=[(sol.t, projected_peatland_emissions/1e6),
           (sol.t, - peatland_annual_carbon_sequestration/1e6)],
    labels=["Peatland Emissions", "Peatland Carbon Sequestration"],
    xlabel="Year", ylabel="Million tCO$_2$eq",
    title="Annual Net Emissions from Peatland",
    #save_as="peatland_emissions_over_time.pdf"
)

# Plot Annual Net Woodland Emissions Over Time 
st.subheader("Annual Net Emissions from Woodland")
plot_fill_between(
    pairs=[(sol.t, woodland_net_emissions/1e6)],
    labels=["Net Emissions from Woodland"],
    xlabel="Year", ylabel="Million tC",
    title="Annual Net Emissions from Woodland Over Time",
)

# Plot inflation index over time
st.subheader("Inflation Index Over Time (2019 = 106.3)")
simple_plot(
    x=sol.t, y=dynamic_inflation_index,
    xlabel="Year", ylabel="Inflation Index",
    title="Inflation Index Over Time",
    label="Inflation Index",
    #save_as="inflation_index_over_time.pdf"
)

# Plot wage growth over time
st.subheader("Wage Growth Index Over Time (2019 = 106.3)")
simple_plot(
    x=sol.t, y=dynamic_wage_growth_index,
    xlabel="Year", ylabel="Wage Growth Index",
    title="Wage Growth Over Time",
    label="Wage Growth",
    #save_as="wage_growth_over_time.pdf"
)

# Plot stagnation of wages relative to inflation over time
st.subheader("Wage Stagnation relative to Inflation Over Time (2019 = 100)")
simple_plot(
    x=sol.t, y=[dynamic_wage_growth_index[i]/dynamic_inflation_index[i] for i in range(len(dynamic_inflation_index))],
    xlabel="Year", ylabel="Wage Stagnation Index",
    title="Wage Stagnation Over Time",
    label="Wage Stagnation",
    #save_as="wage_stagnation_over_time.pdf"
)

# Plot normalised household income shares (static)
st.subheader("Cumulative Equalised Household Income Shares (BHC) in 2019")
plot_histogram_dict(
    data_dict=BHC_cumulative_income_shares,
    xlabel="Decile", ylabel="Cumulative Income Share (\%)",
    title="Cumulative Household Income Shares (BHC)",
    #save_as="normalised_household_income_shares_BHC.pdf"
)

# Plot average income per week by decile
st.subheader("Average Income per Week by Decile")
plot_multiple_histogram_dict(
    data_dict_list=[average_income_dict_final, average_income_dict_initial],
    xlabel="Decile", ylabel="Average Income per Week (£)",
    title="Average Income per Person per Week by Decile (BHC)",
    labels=["2050", "2019"],
    #save_as="average_income_per_week_by_decile_BHC.pdf"
) 

# Plot food cost per capita over time
st.subheader("Food Cost per Capita Over Time")
simple_plot(
    x=sol.t, y=dynamic_food_cost,
    xlabel="Year", ylabel="Food Cost per Capita (£/week)",
    title="Food Cost per Capita Over Time",
    label="Food Cost per Capita",
    #save_as="food_cost_per_capita_over_time.pdf"
)   

# Plot food poverty index over time
st.subheader("Projected Food Poverty Index Over Time")
simple_plot(
    x=sol.t, y=projected_food_poverty_index_array,
    xlabel="Year", ylabel="Food Poverty Index (\%)",
    title="Projected Food Poverty Index Over Time",
    label="Food Poverty Index",
    #save_as="food_poverty_index_over_time.pdf"
)

# Plot y_dudt_food_cost_array vs yhat_dudt_food_cost_array
st.subheader("Food Cost Observed vs Predicted Values (MSE = {:.3f}, NRMSE = {:.3f})".format(mse_food_cost, nrmse_food_cost))
plot_multiple_xy(
    pairs=[(np.array([int(year) for year in food_cost_per_capita_series.keys()]), y_dudt_food_cost_array),
           (np.array([int(year) for year in food_cost_per_capita_series.keys()]), yhat_dudt_food_cost_array)],
    xlabel="Year", ylabel="Food Cost Dudt",
    title="Food Cost Dudt vs Fitted Values",
    labels=["Food Cost Dudt", "Fitted Food Cost Dudt"],
    scatter=True
    #save_as="food_cost_dudt_vs_fitted.pdf"
)


