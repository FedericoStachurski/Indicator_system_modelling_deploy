'''
Useful commands to run this app:
python3  -m venv streamlitEnv
source streamlitEnv/bin/activate
pip3 install -r requirements.txt
python3 -m streamlit run app.py

'''
###############################################
import streamlit as st

###############################################
'''Funtions'''
def compute_total_land_ha(food_production_dict, yield_per_hectare):
    # Function to compute total land in hectares
    total_land_ha = 0
    for item in food_production_dict:
        prod_t = food_production_dict[item] # production in tonnes
        yield_t_per_ha = yield_per_hectare[item]
        land = prod_t / yield_t_per_ha
        total_land_ha += land
    return total_land_ha

def compute_yield_t_per_ha(food_production_dict, land_ha):
    # Function to compute yield estimates in tonnes per hectare
    total_prod = 0
    for item in food_production_dict:
        prod_t = food_production_dict[item]
        total_prod += prod_t
    
    yield_per_hectare = total_prod / land_ha
    return yield_per_hectare

def compute_total_food_production(yield_t_per_ha, land_ha): 
    # Function to compute the total food production in tonnes for each category
    return yield_t_per_ha * land_ha 

def recompute_food__production_dict(total_food_production, food_production_dict, yield_overestimate_factor):
    # Function to (re)compute the food production dictionary in tonnes based on
    # (1) total food production and (2) distribution of food commodities in the prescribed dictionary
    recomputed_dict = {}
    summed_production = sum(food_production_dict.values())
    for item in food_production_dict:
        item_percentage = food_production_dict[item] / summed_production
        recomputed_dict[item] = total_food_production * item_percentage / yield_overestimate_factor
    return recomputed_dict  

def compute_total_calories(food_production_dict, food_calories_per_tonne):
    # Function to compute the total calories in kilo calories for each category
    total_calories = 0
    for item in food_production_dict:
        prod_t = food_production_dict[item]  # production in tonnes
        calories_per_tonne = food_calories_per_tonne[item]
        total_calories += prod_t * calories_per_tonne / 1_000  # convert to kilo calories
    return total_calories

###############################################
'''Dictionaries'''
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
        self.animal_land_ha = total_land_area_by_type["grassland_rough_grazing"]
        self.nonanimal_land_ha = total_land_area_by_type["cereals_oilseeds_potatoes"]
        self.yield_overestimate_factor = 2.0  # Factor to adjust yield estimates for overestimation

# Create instance
parameters = Parameters()
###############################################
# Estimate total yield (in tonnes per hectare) for each land category
animal_yield_t_per_ha = compute_yield_t_per_ha(animal_food_production_dict, parameters.animal_land_ha)
nonanimal_yield_t_per_ha = compute_yield_t_per_ha(nonanimal_food_production_dict, parameters.nonanimal_land_ha)
# Recompute the total land area for animal and non-animal products
recomputed_animal_land_ha = compute_total_land_ha(animal_food_production_dict, yield_per_hectare)
recomputed_nonanimal_land_ha = compute_total_land_ha(nonanimal_food_production_dict, yield_per_hectare)
# Calculate the total food production (in tonnes) for each category
recomputed_animal_total_food_production = compute_total_food_production(animal_yield_t_per_ha, recomputed_animal_land_ha)
recomputed_nonanimal_total_food_production = compute_total_food_production(nonanimal_yield_t_per_ha, recomputed_nonanimal_land_ha)
# Regenerate food production dictionaries based on the total food production
recomputed_animal_food_production_dict = recompute_food__production_dict(recomputed_animal_total_food_production, animal_food_production_dict, parameters.yield_overestimate_factor)
recomputed_nonanimal_food_production_dict = recompute_food__production_dict(recomputed_nonanimal_total_food_production, nonanimal_food_production_dict,  parameters.yield_overestimate_factor)
# Calculate the total food production (in kilo calories) for each category
animal_total_calories = compute_total_calories(recomputed_animal_food_production_dict, food_calories_per_tonne)
nonanimal_total_calories = compute_total_calories(recomputed_nonanimal_food_production_dict, food_calories_per_tonne)

###############################################
# Set the title of the app
st.title("Indicator system modelling: Proof of Concept")

# Create slider
number = st.slider("Select a value", min_value=0, max_value=100, value=50)

# Show the selected value
st.write(f"You selected: {number}")

# Do something with the value — e.g. square it
st.write(f"The square of {number} is {number ** 2}")

#############################################
'''
Useful commands to set up a git repository:
git init
git status
git add app.py requirements.txt
git commit -m "Add simple Streamlit app with slider"
git branch -M main  # or master, depending on your setup
git push -u origin main
'''