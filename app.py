'''
Useful commands to run this app:
python3  -m venv streamlitEnv
source streamlitEnv/bin/activate
pip3 install -r requirements.txt
python3 -m streamlit run app.py


Useful commands to set up a git repository:
git init
git status
git add app.py requirements.txt
git commit -m "Add modelling variables and functions for food production"
git branch -M main 
git push -u origin main
'''
###############################################
import streamlit as st
from scipy import integrate
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
################################################
#set the default font for all figures
font_families = matplotlib.font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Computer Modern']
plt.rcParams['text.usetex'] = True
###############################################
# Functions
def plot_multiple_xy(pairs, xlabel="X", ylabel="Y", title="Multiple Line Plot", labels=None, save_as=None):
    plt.figure(figsize=(5, 3), dpi=150)
    for i, (x, y) in enumerate(pairs):
        label = labels[i] if labels and i < len(labels) else None
        plt.plot(x, y, label=label)

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    if labels:
        plt.legend()
    plt.tight_layout()
    if save_as:
        plt.savefig(save_as, format=save_as.split('.')[-1])
        print(f"Plot saved as '{save_as}'")
    
    st.pyplot(plt)  # <-- Show the plot in Streamlit

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

###############################################
def rhs_animal_land_ha(A, alpha, K, mu):
    rhs = alpha * A * (1 - A/K) - mu * A
    return rhs

def rhs_nonanimal_land_ha(N, A, beta, c, mu):
    rhs = beta * N * (1 - N/c) + mu * A
    return rhs

def all_rhs(t, u, animal_land_growth_rate, K_animal, nonanimal_land_growth_rate, c_nonanimal, mu_landconversion):
    # Function to compute the right-hand side of the system of ODEs
    u_animal_land_ha = u[0]
    u_nonanimal_land_ha = u[1]
    dudt_animal_land_ha = rhs_animal_land_ha(u_animal_land_ha, animal_land_growth_rate, K_animal, mu_landconversion)
    dudt_nonanimal_land_ha = rhs_nonanimal_land_ha(u_nonanimal_land_ha, u_animal_land_ha, nonanimal_land_growth_rate, c_nonanimal, mu_landconversion)
    return [dudt_animal_land_ha, dudt_nonanimal_land_ha]

###############################################
#Dictionaries
animal_food_production_dict = {
    # Food commodity production data in Scotland. This is a crude estimation from the graph. 
    # Source: https://sefari.scot/research/assessing-scotland%E2%80%99s-self-sufficiency-of-major-food-commodities
    # Estimated production in tonnes per year in 2019.
    "Dairy": 1_500_000,
    "Eggs": 1_000_000,
    "Pork": 400_000,
    "Poultry": 200_000,
    "Beef": 150_000,
    "Lamb": 100_000
}

nonanimal_food_production_dict = {
    # Food commodity production data in Scotland. This is a crude estimation from the graph. 
    # Source: https://sefari.scot/research/assessing-scotland%E2%80%99s-self-sufficiency-of-major-food-commodities
    # Estimated production in tonnes per year in 2019.
    "Barley": 2_700_000,
    "Potatoes": 1_500_000,
    "Oats": 600_000,
    "Wheat": 750_000,
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

###############################################
class Parameters:
    # Define a class to hold the parameters
    def __init__(self):
        self.initial_year = 2019  # Initial year for the model
        self.final_year = 2050    # Final year for the model
        self.initial_animal_land_ha = total_land_area_by_type["grassland_rough_grazing"]
        self.initial_nonanimal_land_ha = total_land_area_by_type["cereals_oilseeds_potatoes"]
        self.yield_overestimate_factor = 2.0  # Factor to adjust yield estimates for overestimation
        self.conversion_rate_animal_to_nonanimal_land = 1/1000  # Conversion rate from animal to non-animal land
        self.carry_capacity_animal_initial = 5_000_000  # Carrying capacity for animal land in hectares (for zero conversion rate)
        self.carry_capacity_nonanimal_initial = 2_000_000  # Carrying capacity for non-animal land in hectares (for zero conversion rate)
        self.animal_land_growth_rate = 1/1000  # Growth rate for animal land
        self.nonanimal_land_growth_rate = 1/10000   # Growth rate for non-animal land

# Create instance
parameters = Parameters()
###############################################
# Set the title of the app
st.title("Indicator system modelling: Proof of Concept")

conversion_rate_slider = st.slider("Select a value", min_value=0.0, max_value=0.01, value=parameters.conversion_rate_animal_to_nonanimal_land, step=0.0001)
st.write(f"You selected a conversion rate of: {conversion_rate_slider}. Please wait while the model is running...")

sol = integrate.solve_ivp(
    all_rhs, 
    [parameters.initial_year, parameters.final_year], 
    [parameters.initial_animal_land_ha, parameters.initial_nonanimal_land_ha],
    args=(parameters.animal_land_growth_rate, parameters.carry_capacity_animal_initial, 
          parameters.nonanimal_land_growth_rate, parameters.carry_capacity_nonanimal_initial, 
          conversion_rate_slider),
    t_eval=np.arange(parameters.initial_year, parameters.final_year + 1, 1),
    method='RK45'
)

dynamic_animal_land_ha = sol.y[0]
dynamic_nonanimal_land_ha = sol.y[1]
###############################################
# Estimate total yield (in tonnes per hectare) for each land category
animal_yield_t_per_ha = compute_yield_t_per_ha(animal_food_production_dict, parameters.initial_animal_land_ha)
nonanimal_yield_t_per_ha = compute_yield_t_per_ha(nonanimal_food_production_dict, parameters.initial_nonanimal_land_ha)
# Create a dictionary for area percentage for each produce type
animal_area_percentage_dict = create_area_percentage_dict(animal_food_production_dict, animal_yield_t_per_ha, parameters.initial_animal_land_ha)
nonanimal_area_percentage_dict = create_area_percentage_dict(nonanimal_food_production_dict, nonanimal_yield_t_per_ha, parameters.initial_nonanimal_land_ha)
###############################################
# Dynamic variables
# Dynamic food production dictionaries
dynamic_animal_food_production_dict = create_food_production_dict(animal_yield_t_per_ha, dynamic_animal_land_ha, animal_area_percentage_dict)
dynamic_nonanimal_food_production_dict = create_food_production_dict(nonanimal_yield_t_per_ha, dynamic_nonanimal_land_ha, nonanimal_area_percentage_dict)
# Total food production (in tonnes)
dynamic_animal_total_food_production = sum(dynamic_animal_food_production_dict.values())
dynamic_nonanimal_total_food_production = sum(dynamic_nonanimal_food_production_dict.values())
# Calculate the total food production (in kilo calories)
dynamic_animal_total_calories = compute_total_calories(dynamic_animal_food_production_dict, food_calories_per_tonne)
dynamic_nonanimal_total_calories = compute_total_calories(dynamic_nonanimal_food_production_dict, food_calories_per_tonne)
###############################################
# Plot the results
# Plot land area over time
st.subheader("Land Area Over Time")
plot_multiple_xy(
    pairs=[(sol.t, dynamic_animal_land_ha/1e6), (sol.t, dynamic_nonanimal_land_ha/1e6)],
    labels=["Animal Land", "Non-Animal Land"],
    xlabel="Year", ylabel="Million Hectares",
    title="Land Area Over Time",
    #save_as="land_area_over_time.pdf"
)

# Plot food production over time in mass
st.subheader("Food Production (mass)")
plot_multiple_xy(
    pairs=[(sol.t, dynamic_animal_total_food_production/1e6), 
           (sol.t, dynamic_nonanimal_total_food_production/1e6)],
    labels=["Animal Food Production", "Non-Animal Food Production"],
    xlabel="Year", ylabel="Million Tonnes",
    title="Food Production in tonnes",
    #save_as="food_production_mass.pdf"
)   

# Plot food production over time in calories
st.subheader("Food Production (energy content)")
plot_multiple_xy(
    pairs=[(sol.t, dynamic_animal_total_calories//1e9), 
           (sol.t, dynamic_nonanimal_total_calories//1e9)],
    labels=["Animal Food Production", "Non-Animal Food Production"],
    xlabel="Year", ylabel="Trillion calories",
    title="Food Production in calories",
    #save_as="food_production_calories.pdf"
)