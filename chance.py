import requests
import json 

def calculate_lottery_chances(lottery_data):
    # Calculate subscriber group sizes based on assumptions
    non_priority_subscribers = lottery_data['total_subscribers'] - lottery_data['disabled_subscribers'] - lottery_data['local_subscribers']
    combat_subscribers = non_priority_subscribers * 0.25
    non_combat_subscribers = non_priority_subscribers * 0.25
    general_public_subscribers = non_priority_subscribers * 0.5

    remaining_apartments = lottery_data['total_apartments']

    # Stage 1: Disabled
    disabled_pool = lottery_data['disabled_subscribers']
    chance_disabled = lottery_data['reserved_disabled'] / disabled_pool if disabled_pool > 0 else 0
    winners_disabled = min(disabled_pool, lottery_data['reserved_disabled'])
    remaining_apartments -= winners_disabled
    rollover_disabled = disabled_pool - winners_disabled

    # Stage 2: Combat Reservists
    chance_combat = lottery_data['reserved_combat'] / combat_subscribers if combat_subscribers > 0 else 0
    winners_combat = min(combat_subscribers, lottery_data['reserved_combat'])
    remaining_apartments -= winners_combat
    rollover_combat = combat_subscribers - winners_combat

    # Stage 3: Non-Combat Reservists (includes combat rollovers)
    apartments_non_combat = lottery_data['reserved_reservists_total'] - lottery_data['reserved_combat']
    non_combat_pool = non_combat_subscribers + rollover_combat
    chance_non_combat = apartments_non_combat / non_combat_pool if non_combat_pool > 0 else 0
    winners_non_combat = min(non_combat_pool, apartments_non_combat)
    remaining_apartments -= winners_non_combat
    rollover_reservists = non_combat_pool - winners_non_combat

    # Stage 5: General Public (all remaining participants)
    general_pool = general_public_subscribers + rollover_disabled + rollover_reservists + lottery_data['local_subscribers']
    chance_general = remaining_apartments / general_pool if general_pool > 0 else 0

    # Calculate total probability for each starting group
    # return {
    #     "Disabled": chance_disabled + (1 - chance_disabled) * chance_general,
    #     "Combat Reservist": chance_combat + (1 - chance_combat) * chance_non_combat + (1 - chance_combat) * (1 - chance_non_combat) * chance_general,
    #     "Non-Combat Reservist": chance_non_combat + (1 - chance_non_combat) * chance_general,
    #     "Local Resident": chance_general,
    #     "General Public": chance_general
    # }
    return chance_combat + (1 - chance_combat) * chance_non_combat + (1 - chance_combat) * (1 - chance_non_combat) * chance_general

# Define the API endpoint
api_url = "https://www.dira.moch.gov.il/api/Invoker?method=Projects&param=%3FfirstApplicantIdentityNumber%3D%26secondApplicantIdentityNumber%3D%26ProjectStatus%3D4%26Entitlement%3D1%26PageNumber%3D1%26PageSize%3D100%26IsInit%3Dtrue%26"

# Make a GET request
response = requests.get(api_url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response into a Python dictionary
    data = response.json()

    #disabled_city_codes = [7100,9000,3000,2610,2200,99,6700,2630,1061,478]
    disabled_city_codes = []

    available_cities = {}

    for project in data["ProjectItems"]:
        if project['CityCode'] not in disabled_city_codes:
            available_cities[project['CityCode']] = 1

    for project in data["ProjectItems"]:
        if project['CityCode'] not in disabled_city_codes:
            lottery_parameters = {
                "total_apartments": project['TargetHousingUnits'],
                "reserved_disabled": project['HousingUnitsForHandicapped'],
                "reserved_combat": project['HU_CombatReservist_L'],
                "reserved_reservists_total": project['HU_Reservists_L'],
                "total_subscribers": project['TotalSubscribers'],
                "disabled_subscribers": project['TotalHandicappedSubscribers'],
                "local_subscribers": project['TotalLocalSubscribers']
            }

            chances_at_lottery = calculate_lottery_chances(lottery_parameters)
            available_cities[project['CityCode']] = available_cities[project['CityCode']] * (1-chances_at_lottery)

    for project in data["ProjectItems"]:
        if project['CityCode'] not in disabled_city_codes:
            lottery_parameters = {
                "total_apartments": project['TargetHousingUnits'],
                "reserved_disabled": project['HousingUnitsForHandicapped'],
                "reserved_combat": project['HU_CombatReservist_L'],
                "reserved_reservists_total": project['HU_Reservists_L'],
                "total_subscribers": project['TotalSubscribers'],
                "disabled_subscribers": project['TotalHandicappedSubscribers'],
                "local_subscribers": project['TotalLocalSubscribers']
            }
            city_chance = 1 - available_cities[project['CityCode']]
            chances_at_lottery = calculate_lottery_chances(lottery_parameters)
            print(f"Lottery: {project['LotteryNumber']}, CityCode: {project['CityCode']}, City: {project['CityDescription']}, PricePerUnit: {project['PricePerUnit']*100}, Total Units: {project['TargetHousingUnits']}, Total Subscribers: {project['TotalSubscribers']}, Chances: {chances_at_lottery:.4%}, Total City Chance: {city_chance:.4%}")