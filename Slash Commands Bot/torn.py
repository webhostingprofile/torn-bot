from datetime import datetime
import requests
import os 
from dotenv import load_dotenv
from database import execute_query, fetch_query, fetch_user_key

load_dotenv()
TOKEN= os.getenv('torn_api_key')
DISCORD_ID=os.getenv('DISCORD_ID')
print("Torn token = ", TOKEN)
print("DISCORD_ID = ", DISCORD_ID)

def get_user_details():

    url = f'https://api.torn.com/user/?selections=profile&key={TOKEN}'
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            user_data = response.json()
            print("user data from user details = ", user_data);
            status = user_data.get('status', {})
            user_details = (
                f"User Details:\n"
                f"Username: {user_data['name']}\n"
                f"Level: {user_data['level']}\n"
                f"Status: {status.get('description', 'Unknown')}\n"
                f"State: {status.get('state', 'Unknown')}\n"
                f"Color: {status.get('color', 'Unknown')}\n"
                f"Until: {status.get('until', 'Unknown')}\n"
            )
            return user_details
        else:
            return f"Error fetching data: {response.status_code}"
    
    except requests.exceptions.RequestException as e:
        return f"Error fetching data: {e}"

import requests
from database import fetch_user_key, fetch_query, execute_query

def get_user_stats(discord_id):
    discord_id=str(discord_id)
    print("discord_id", discord_id)
    print("user keys fetched", fetch_user_key(discord_id))
    torn_api_key = fetch_user_key(discord_id)[1] # api key at index 1 from comment line below
    if not torn_api_key:
        return "Torn API key not found for the user"
    print("torn api key = ", torn_api_key)
    #torn api key =  ('745436062322524160', 'yekdYV2PE5kItBBN', '2672120')
    url = f'https://api.torn.com/user/?selections=battlestats&key={torn_api_key}'

    try:
        response = requests.get(url)
        if response.status_code == 200:
            user_data = response.json()
            current_stats = {
                'strength': user_data.get('strength', 0),
                'speed': user_data.get('speed', 0),
                'defense': user_data.get('defense', 0),
                'dexterity': user_data.get('dexterity', 0)
            }

            # Calculate total of current stats
            total = sum(current_stats.values())

            # Fetch previous stats from the database
            query = "SELECT strength, speed, defense, dexterity, total FROM user_stats WHERE discord_id = %s"
            params = (discord_id,)
            result = fetch_query(query, params)

            if result:
                previous_stats = {
                    'strength': result[0],
                    'speed': result[1],
                    'defense': result[2],
                    'dexterity': result[3],
                    'total': result[4]
                }

                # Calculate change and percentage change
                change_in_stats = ""
                percentage_change = ""
                for stat in ['strength', 'speed', 'defense', 'dexterity']:
                    if previous_stats[stat] != 0:
                        change = current_stats[stat] - previous_stats[stat]
                        percent_change = ((current_stats[stat] - previous_stats[stat]) / previous_stats[stat]) * 100
                    else:
                        change = current_stats[stat]
                        percent_change = 100 if current_stats[stat] > 0 else 0

                    change_in_stats += f"{stat.capitalize()}: {change:,}\n"
                    percentage_change += f"{stat.capitalize()}: {percent_change:.2f}%\n"

                total_change = total - previous_stats['total']
                total_percent_change = ((total - previous_stats['total']) / previous_stats['total']) * 100 if previous_stats['total'] != 0 else 100

                change_in_stats += f"Total: {total_change:,}\n"
                percentage_change += f"Total: {total_percent_change:.2f}%\n"

                comparison = (
                    f"Comparison with last recorded stats:\n"
                    f"Strength: {previous_stats['strength']:,} → {current_stats['strength']:,}\n"
                    f"Speed: {previous_stats['speed']:,} → {current_stats['speed']:,}\n"
                    f"Defense: {previous_stats['defense']:,} → {current_stats['defense']:,}\n"
                    f"Dexterity: {previous_stats['dexterity']:,} → {current_stats['dexterity']:,}\n"
                    f"Total: {previous_stats['total']:,} → {total:,}\n"
                )
            else:
                change_in_stats = "No previous stats found for change calculation."
                percentage_change = ""
                comparison = "No previous stats found for comparison."

            # Store the new stats in the database
            query = """
            INSERT INTO user_stats (discord_id, last_call, strength, speed, defense, dexterity, total)
            VALUES (%s, current_timestamp, %s, %s, %s, %s, %s)
            ON CONFLICT (discord_id) DO UPDATE
            SET last_call = current_timestamp,
                strength = EXCLUDED.strength,
                speed = EXCLUDED.speed,
                defense = EXCLUDED.defense,
                dexterity = EXCLUDED.dexterity,
                total = EXCLUDED.total
            """
            params = (discord_id, current_stats['strength'], current_stats['speed'], current_stats['defense'], current_stats['dexterity'], total)
            execute_query(query, params)

            # Return formatted stats, change, percentage change, and comparison
            user_details = (
                f"Battle Stats:\n"
                f"Strength: {current_stats['strength']:,}\n"
                f"Speed: {current_stats['speed']:,}\n"
                f"Defense: {current_stats['defense']:,}\n"
                f"Dexterity: {current_stats['dexterity']:,}\n"
                f"Total: {total:,}\n"
                f"\nChange in Stats:\n{change_in_stats}"
                f"\nPercentage Change:\n{percentage_change}"
                f"\n{comparison}"
            )
            return user_details
        else:
            return f"Error fetching data: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Error fetching data: {e}"


    
def get_user_profile():
    url=f'https://api.torn.com/user/?selections=profile&key={TOKEN}'

    try:
        response = requests.get(url)
        if response.status_code == 200:
            user_data = response.json()
            print("user profile data ", user_data)
            profile_formatted = format_torn_profile(user_data)
            return profile_formatted
        else:
            return f"Error fetching data: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Error fetching data: {e}"
    


def format_torn_profile(data):
    # Extracting and formatting the necessary details
    profile = {
        'name': data['name'],
        'player_id': data['player_id'],
        'role': data['role'],
        'level': data['level'],
        'rank': data['rank'],
        'age': f"{data['age'] // 365} years {data['age'] % 365 // 30} months {data['age'] % 30} days old",
        'last_online': datetime.datetime.fromtimestamp(data['last_action']['timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
        'life': f"{data['life']['current']}/{data['life']['maximum']}",
        'status': data['status']['description'],
        'employment': f"{data['job']['position']} at {data['job']['company_name']}",
        'faction': f"{data['faction']['position']} of {data['faction']['faction_name']}",
        'marriage': f"Married to {data['married']['spouse_name']} for {data['married']['duration']} days",
        'property': data['property'],
        'networth': '$4,178m',  # This is a static value from the image, you might want to calculate it dynamically
        'awards': data['awards'],
        'friends': data['friends'],
        'enemies': data['enemies'],
        'forum_posts': data['forum_posts'],
        'karma': data['karma'],
        'profile_image': data['profile_image']
    }

    # Formatting the output to match the image
    formatted_profile = f"""
    Profile for {profile['name']}[{profile['player_id']}]
    {profile['role']} - Level {profile['level']}, {profile['rank']}
    {profile['age']}
    Last online {profile['last_online']}
    
    💙 Status {profile['life']}
    ✅ {profile['status']}
    
    🧑 Employment
    {profile['employment']}
    
    ⚔️ Faction
    {profile['faction']}
    
    ❤️ Marriage
    {profile['marriage']}
    
    Property: {profile['property']}
    
    📊 Social Statistics
    Networth: {profile['networth']}
    Awards: {profile['awards']}
    Friends: {profile['friends']}
    Enemies: {profile['enemies']}
    
    💬 Forum Statistics
    Forum Posts: {profile['forum_posts']}
    Karma: {profile['karma']}
    
    Links
    Trade | Display Cabinet | Bazaar | Bounty | Attack
    """
    return formatted_profile

def get_vitals():
    url=f'https://api.torn.com/user/?selections=profile,properties,personalstats,cooldowns,bars,education&key={TOKEN}'

    try:
        response = requests.get(url)
        if response.status_code == 200:
            user_data = response.json()
            print("user vitals data ", user_data)
            vitals_formatted = format_vitals(user_data)
            return vitals_formatted
        else:
            return f"Error fetching data: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Error fetching data: {e}"

def format_vitals(data):
    # Extracting and formatting the necessary details
    vitals = {
        'life': f"{data['life']['current']}/{data['life']['maximum']}",
        'energy': f"{data['energy']['current']}/{data['energy']['maximum']}",
        'happiness': f"{data['happy']['current']}/{data['happy']['maximum']}",
        'nerve': f"{data['nerve']['current']}/{data['nerve']['maximum']}",
        'nerve_full': data['nerve']['fulltime'],
        'medical_cooldown': data['cooldowns']['medical'],
        'drug_cooldown': data['cooldowns']['drug'],
        'booster_cooldown': data['cooldowns']['booster'],
        'education_cooldown': data['education_timeleft'] #data['cooldowns']['education'],
    }

    # Converting seconds to readable format
    def format_time(seconds):
        if seconds == 0:
            return "None"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            minutes = (seconds % 3600) // 60
            return f"{days}d {hours}h {minutes}m" if days else f"{hours}h {minutes}m"

    formatted_vitals = f"""
    Vitals for {data['name']}[{data['player_id']}]

    Life
    {vitals['life']}

    Energy
    {vitals['energy']}

    Happiness
    {vitals['happiness']}

    Nerve
    {vitals['nerve']}
    Full in {format_time(vitals['nerve_full'])}

    Medical Cooldown
    {format_time(vitals['medical_cooldown'])}

    Drug Cooldown
    {format_time(vitals['drug_cooldown'])}

    Booster Cooldown
    {format_time(vitals['booster_cooldown'])}

    Education Cooldown
    {format_time(vitals['education_cooldown'])}
    """
    return formatted_vitals


def get_eta():
    url = f'https://api.torn.com/user/?selections=travel&key={TOKEN}'

    try:
        response = requests.get(url)
        if response.status_code == 200:
            user_data = response.json()
            travel_data = user_data.get('travel', {})
            destination = travel_data.get('destination')
            time_left = travel_data.get('time_left')

            if destination and time_left is not None:
                print("date time current = ", datetime.now())
                time = datetime.now()
                current_time = time.strftime('%H:%M:%S')
                print("current_time = ", current_time)
                ##arrival_time = current_time + datetime.timedelta(seconds=time_left)

                #formatted_current_time = current_time.strftime("%H:%M")
                # = arrival_time.strftime("%H:%M")
                
                formatted_time_left = format_time_left(time_left)
                # need to add link in to take their profile 
                # also need to check if they are arrived then to show landed in destination
                output = f"✈️ Traveling to {destination}\nEstimate Arrival\n{current_time} ({formatted_time_left})"
                return output
            else:
                return "Error: Incomplete travel data received"
        else:
            return f"Error fetching data: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Error fetching data: {e}"
    
def format_time_left(seconds):
    days, seconds = divmod(seconds, 86400)  # 86400 seconds in a day
    hours, seconds = divmod(seconds, 3600)  # 3600 seconds in an hour
    minutes, seconds = divmod(seconds, 60)  # 60 seconds in a minute

    time_left_str = []
    if days > 0:
        time_left_str.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        time_left_str.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        time_left_str.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds > 0 or len(time_left_str) == 0:
        time_left_str.append(f"{seconds} second{'s' if seconds != 1 else ''}")

    return ", ".join(time_left_str)

def run_torn_commands():
    get_user_details()