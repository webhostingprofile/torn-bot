from datetime import datetime, timedelta, timezone
import requests
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from database import get_firestore_db
import pytz

load_dotenv()
TOKEN = os.getenv('torn_api_key')
DISCORD_ID = os.getenv('DISCORD_ID')
print("Torn token = ", TOKEN)
print("DISCORD_ID = ", DISCORD_ID)

# # Create a dictionary with the environment variables
# firebase_credentials = {
#     "type": os.getenv("FIREBASE_TYPE"),
#     "project_id": os.getenv("FIREBASE_PROJECT_ID"),
#     "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
#     "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
#     "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
#     "client_id": os.getenv("FIREBASE_CLIENT_ID"),
#     "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
#     "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
#     "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
#     "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL"),
#     "universe_domain": os.getenv("UNIVERSE_DOMAIN"),
# }

# # Initialize Firebase app
# cred = credentials.Certificate(firebase_credentials)
# firebase_admin.initialize_app(cred)

def get_user_profile_link(torn_id, link_text):
    url = f'https://www.torn.com/profiles.php?XID={torn_id}'
    return f'[{link_text}]({url})'

def get_user_torn_info(discord_id):
    """
    Retrieve the Torn API key and timezone for a given user from Firestore.

    Parameters:
    discord_id (str): The Discord ID of the user.

    Returns:
    dict: A dictionary containing the 'torn_api_key' and 'time_zone'.
          If an error occurs, returns a dictionary with an 'error' key and message.
    """
    db = get_firestore_db()

    # Fetch Torn API key and user timezone from Firestore
    user_doc = db.collection('user_keys').document(discord_id).get()
    if not user_doc.exists:
        return {'error': "User data not found."}

    user_data = user_doc.to_dict()
    torn_api_key = user_data.get('torn_api_key')
    user_timezone_str = user_data.get('time_zone')
    torn_id = user_data.get('torn_id')
    if not torn_api_key:
        return {'error': "Torn API key not found for the user."}
    
    if not user_timezone_str:
        return {'error': "User timezone not set. Please set your timezone using !timezone command."}

    return {
        'torn_api_key': torn_api_key,
        'time_zone': user_timezone_str,
        'torn_id': torn_id,
    }

def calculate_stat_changes(current_stats, previous_stats):
    change_in_stats = ""
    percentage_change = ""
    
    for stat in ['strength', 'speed', 'defense', 'dexterity']:
        change = current_stats.get(stat, 0) - previous_stats.get(stat, 0)
        previous_stat_value = previous_stats.get(stat, 0)
        percent_change = ((change / previous_stat_value) * 100) if previous_stat_value != 0 else 0

        change_in_stats += f"{stat.capitalize()}: {change:,}\n"
        percentage_change += f"{stat.capitalize()}: {percent_change:.2f}%\n"

    total_current = sum(current_stats.values())
    total_previous = previous_stats.get('total', 0)
    total_change = total_current - total_previous
    total_percent_change = ((total_change / total_previous) * 100) if total_previous != 0 else 0

    change_in_stats += f"Total: {total_change:,}\n"
    percentage_change += f"Total: {total_percent_change:.2f}%\n"

    return change_in_stats, percentage_change, total_current, total_previous


def get_user_details(discord_id):
    discord_id = str(discord_id)
     # Retrieve the Torn API key using the reusable function
    user_info = get_user_torn_info(discord_id)
    if 'error' in user_info:
        return user_info['error']
    
    torn_api_key = user_info['torn_api_key']

    # Use the retrieved API key in the request URL
    url = f'https://api.torn.com/user/?selections=profile&key={torn_api_key}'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            user_data = response.json()
            print("user data from user details = ", user_data)
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

def get_user_stats(discord_id, discord_username):
    discord_id = str(discord_id)

    db = get_firestore_db()  # Use the Firestore client from your database setup

    # Fetch Torn API key and user timezone from Firestore
    user_doc = db.collection('user_keys').document(discord_id).get()
    if user_doc.exists:
        user_data = user_doc.to_dict()
        torn_api_key = user_data.get('torn_api_key')
        user_timezone_str = user_data.get('time_zone')  # Assuming timezone is stored
        torn_id = user_data.get('torn_id')
    else:
        return "User data not found."

    if not torn_api_key:
        return "Torn API key not found for the user."
    
    if not user_timezone_str:
        return "User timezone not set. Please set your timezone using !timezone command."

    # Fetch current user stats from Torn API
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

            total = sum(current_stats.values())

            # Fetch previous stats from Firestore
            stats_doc = db.collection('user_stats').document(discord_id).get()
            if stats_doc.exists:
                previous_stats = stats_doc.to_dict()
                previous_stats['total'] = previous_stats.get('total', 0)

                # Calculate changes and percentage changes
                changes = {}
                for stat in ['strength', 'speed', 'dexterity', 'defense']:
                    change = current_stats[stat] - previous_stats.get(stat, 0)
                    percent_change = ((change / previous_stats[stat]) * 100) if previous_stats[stat] != 0 else 0
                    changes[stat] = (change, percent_change)

                total_change = total - previous_stats['total']
                total_percent_change = ((total_change / previous_stats['total']) * 100) if previous_stats['total'] != 0 else 0

                # Format the last_call timestamp for display
                if 'last_call' in previous_stats:
                    last_call_timestamp = previous_stats['last_call']
                    formatted_last_call = last_call_timestamp.strftime('%d %B %Y at %H:%M:%S')
                else:
                    formatted_last_call = "N/A"

                link_text = f"Changes to Stats for {discord_username}"
                profile_link = get_user_profile_link(torn_id, link_text)

                # Formatted output for Discord
                user_details = (
                    f"{profile_link}:\n\n"
                    f"Old Battle Stats ---> New Battle Stats\n"
                    f"Str: {previous_stats.get('strength', 0):,} ---> {current_stats['strength']:,} ({changes['strength'][0]:,} ({changes['strength'][1]:.2f}%))\n"
                    f"Spd: {previous_stats.get('speed', 0):,} ---> {current_stats['speed']:,} ({changes['speed'][0]:,} ({changes['speed'][1]:.2f}%))\n"
                    f"Dex: {previous_stats.get('dexterity', 0):,} ---> {current_stats['dexterity']:,} ({changes['dexterity'][0]:,} ({changes['dexterity'][1]:.2f}%))\n"
                    f"Def: {previous_stats.get('defense', 0):,} ---> {current_stats['defense']:,} ({changes['defense'][0]:,} ({changes['defense'][1]:.2f}%))\n\n"
                    f"Tot: {previous_stats['total']:,} ---> {total:,} ({total_change:,} ({total_percent_change:.2f}%))\n\n"
                    f"Changes since: {formatted_last_call}"
                )
            else:
                user_details = (
                    f"{profile_link}:\n\n"
                    f"Old Battle Stats ---> New Battle Stats\n"
                    f"Str: {previous_stats.get('strength', 0):,}\n"
                    f"Spd: {previous_stats.get('speed', 0):,}\n"
                    f"Dex: {previous_stats.get('dexterity', 0):,}\n"
                    f"Def: {previous_stats.get('defense', 0):,} \n\n"
                    f"Tot: {previous_stats['total']:,}\n\n"
                )
            
            # Store the new stats in Firestore
            db.collection('user_stats').document(discord_id).set({
                'last_call': datetime.utcnow(),
                'strength': current_stats['strength'],
                'speed': current_stats['speed'],
                'defense': current_stats['defense'],
                'dexterity': current_stats['dexterity'],
                'total': total
            }, merge=True)

            return user_details
        else:
            return f"Error fetching data: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Error fetching data: {e}"
    
def get_mentioned_user_stats(mentioned_discord_id, mentioned_discord_username):
    mentioned_discord_id = str(mentioned_discord_id)

    db = get_firestore_db() 

    # Fetch previous stats from Firestore for the mentioned user
    stats_doc = db.collection('user_stats').document(mentioned_discord_id).get()
    if stats_doc.exists:
        previous_stats = stats_doc.to_dict()
        previous_stats['total'] = previous_stats.get('total', 0)

        # Format the last_call timestamp for display
        if 'last_call' in previous_stats:
            last_call_timestamp = previous_stats['last_call']
            formatted_last_call = last_call_timestamp.strftime('%d %B %Y at %H:%M:%S')
        else:
            formatted_last_call = "N/A"

        link_text = f"Stats for {mentioned_discord_username}"
        profile_link = get_user_profile_link(previous_stats.get('torn_id', 'N/A'), link_text)
        # Formatted output for Discord
        user_details = (
            f"{profile_link}:\n\n"
            f"Current Battle Stats\n"
            f"Str: {previous_stats.get('strength', 0):,}\n"
            f"Spd: {previous_stats.get('speed', 0):,}\n"
            f"Dex: {previous_stats.get('dexterity', 0):,}\n"
            f"Def: {previous_stats.get('defense', 0):,}\n\n"
            f"Tot: {previous_stats['total']:,}\n\n"
            f"Last updated: {formatted_last_call}"  # display formatted timestamp
        )

        return user_details
    else:
        return "Stats not found for the mentioned user."


# Function to get user stats and their percentage makeup
def get_user_stats_as_percentage(discord_id, discord_username):
    discord_id = str(discord_id)

    db = get_firestore_db()  # Use the Firestore client from your database setup
 
    # Fetch Torn API key and user timezone from Firestore
    user_doc = db.collection('user_keys').document(discord_id).get()
    if user_doc.exists:
        user_data = user_doc.to_dict()
        torn_api_key = user_data.get('torn_api_key')
        user_timezone_str = user_data.get('time_zone')  # Assuming timezone is stored
        torn_id = user_data.get('torn_id')
    else:
        return "User data not found."

    if not torn_api_key:
        return "Torn API key not found for the user."
    
    if not user_timezone_str:
        return "User timezone not set. Please set your timezone using !timezone command."

    # Fetch current user stats from Torn API
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

            total = sum(current_stats.values())

            # Fetch previous stats from Firestore
            stats_doc = db.collection('user_stats').document(discord_id).get()
            if stats_doc.exists:
                previous_stats = stats_doc.to_dict()
                previous_stats['total'] = previous_stats.get('total', 0)
            else:
                previous_stats = {}

            # Calculate percentage makeup of each stat
            stat_percentages = {stat: (value / total * 100) if total > 0 else 0 for stat, value in current_stats.items()}

            # Format the last_call timestamp for display
            if 'last_call' in previous_stats:
                last_call_timestamp = previous_stats['last_call']
                formatted_last_call = last_call_timestamp.strftime('%d %B %Y at %H:%M:%S')
            else:
                formatted_last_call = "N/A"

            link_text = f"Stats for {discord_username}"
            profile_link = get_user_profile_link(torn_id, link_text)

            # Formatted output for Discord
            user_details = (
                f"{profile_link}:\n\n"
                f"Current Battle Stats\n"
                f"Str: {current_stats['strength']:,} ({stat_percentages['strength']:.2f}%)\n"
                f"Spd: {current_stats['speed']:,} ({stat_percentages['speed']:.2f}%)\n"
                f"Dex: {current_stats['dexterity']:,} ({stat_percentages['dexterity']:.2f}%)\n"
                f"Def: {current_stats['defense']:,} ({stat_percentages['defense']:.2f}%)\n\n"
                f"Total: {total:,}\n\n"
                f"Last updated: {formatted_last_call}"
            )

            return user_details

        else:
            return f"Error fetching data: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Error fetching data: {e}"

def get_user_stat_history(discord_id, discord_username, days_ago):
    discord_id = str(discord_id)
    db = get_firestore_db()
    user_doc = db.collection('user_keys').document(discord_id).get()
    if user_doc.exists:
        user_data = user_doc.to_dict()
        torn_api_key = user_data.get('torn_api_key')
        user_timezone_str = user_data.get('time_zone')
        torn_id = user_data.get('torn_id')
    else:
        return "User data not found."
    
    if not torn_api_key:
        return "Torn API key not found for the user."
    
    if not user_timezone_str:
        return "User timezone not set. Please set your timezone using !timezone command."

    # Get current battle stats
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

    except requests.exceptions.RequestException as e:
        return f"Error fetching data: {e}"

    # Get historical stats for the specified date
    target_date = datetime.utcnow() - timedelta(days=days_ago)
    unix_timestamp = int(target_date.timestamp())
    url = f'https://api.torn.com/user/?key={torn_api_key}&timestamp={unix_timestamp}&stat=strength,defense,speed,dexterity,totalstats&comment=TornAPI&selections=personalstats'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            user_data = response.json()
            personal_stats = user_data.get('personalstats', {})
            previous_stats = {
                'strength': personal_stats.get('strength', 0),
                'speed': personal_stats.get('speed', 0),
                'defense': personal_stats.get('defense', 0),
                'dexterity': personal_stats.get('dexterity', 0),
                'total': personal_stats.get('totalstats', sum(personal_stats.values()))
            }

            # Calculate changes
            change_in_stats, percentage_change, total_current, total_previous = calculate_stat_changes(current_stats, previous_stats)

            link_text = f"Battle Stat changes for {discord_username}"
            profile_link = get_user_profile_link(torn_id, link_text)
            formatted_date = target_date.strftime('%d %B %Y')
            stats_details = (
                f"{profile_link}:\n\n"
                f"Strength: {previous_stats['strength']:,}\n"
                f"Speed: {previous_stats['speed']:,}\n"
                f"Defense: {previous_stats['defense']:,}\n"
                f"Dexterity: {previous_stats['dexterity']:,}\n"
                f"Total: {previous_stats['total']:,}\n\n"
                f"Current Stats:\n"
                f"Strength: {current_stats['strength']:,}\n"
                f"Speed: {current_stats['speed']:,}\n"
                f"Defense: {current_stats['defense']:,}\n"
                f"Dexterity: {current_stats['dexterity']:,}\n"
                f"Total: {total_current:,}\n\n"
                f"Change in Stats:\n{change_in_stats}"
                f"\nPercentage Change:\n{percentage_change}"
                 f"Changes Since: {formatted_date}:\n"
            )

            return stats_details
        else:
            return f"Error fetching data: {response.status_code}"
        
    except requests.exceptions.RequestException as e:
        return f"Error fetching data: {e}"

def get_user_work_stats(discord_id):
    discord_id = str(discord_id)

    user_info = get_user_torn_info(discord_id)
    if 'error' in user_info:
        return user_info['error']
    
    # Retrieve api key 
    torn_api_key = user_info['torn_api_key']
    torn_id = user_info['torn_id']

    url = f'https://api.torn.com/user/?selections=workstats&key={torn_api_key}'

    try: 
        response = requests.get(url)
        if response.status_code == 200:
            user_data = response.json()
            work_stats = {
                'manual_labor': user_data.get('manual_labor', 0),
                'intelligence': user_data.get('intelligence', 0),
                'endurance': user_data.get('endurance', 0),
            }
        else:
            return f"Error fetching data: {response.status_code}"

    except requests.exceptions.RequestException as e:
        return f'Error fetching data: {e}'
    
    work_stats_formatted = (
        f"Manual Labor: {work_stats['manual_labor']:,}\n"
        f"Intelligence: {work_stats['intelligence']:,}\n"
        f"Endurace: {work_stats['endurance']:,}\n"
    )
    return work_stats_formatted

            #{"manual_labor":20238,"intelligence":40923,"endurance":90845}


def get_user_profile(discord_id, discord_username):
    discord_id = str(discord_id)

    # Retrieve the Torn API key using the reusable function
    user_info = get_user_torn_info(discord_id)
    if 'error' in user_info:
        return user_info['error']
    
    torn_api_key = user_info['torn_api_key']
    torn_id = user_info['torn_id']
    

    # Use the retrieved API key in the request URL
    url = f'https://api.torn.com/user/?selections=profile&key={torn_api_key}'

    try:
        response = requests.get(url)
        if response.status_code == 200:
            user_data = response.json()
            print("user profile data ", user_data)
            link_text = f"Profile Data for {discord_username}"
            profile_link = get_user_profile_link(torn_id, link_text)
            profile_formatted = format_torn_profile(user_data)
            profile_formatted_with_link = f"{profile_link}\n\n{profile_formatted}"
            return profile_formatted_with_link
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
        'last_online': datetime.fromtimestamp(data['last_action']['timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
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

def get_vitals(discord_id):
    discord_id = str(discord_id)
    # Retrieve the Torn API key using the reusable function
    user_info = get_user_torn_info(discord_id)
    if 'error' in user_info:
        return user_info['error']
    
    torn_api_key = user_info['torn_api_key']

    # Use the retrieved API key in the request URL
    url = f'https://api.torn.com/user/?selections=profile,properties,personalstats,cooldowns,bars,education&key={torn_api_key}'

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
        'education_cooldown': data['education_timeleft'] # data['cooldowns']['education'],
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
                formatted_time_left = format_time_left(time_left)
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


def get_effective_battlestats(discord_id, discord_username):
    discord_id = str(discord_id)
    # Retrieve the Torn API key using the reusable function
    user_info = get_user_torn_info(discord_id)
    if 'error' in user_info:
        return user_info['error']
    
    torn_api_key = user_info['torn_api_key']
    torn_id = user_info['torn_id']
    url = f'https://api.torn.com/user/?selections=battlestats&key={torn_api_key}'

    # Make the API call to retrieve battle stats
    response = requests.get(url)
    if response.status_code != 200:
        return f"Error: Unable to fetch data. Status code: {response.status_code}"
    
    battle_stats = response.json()
    
    if 'error' in battle_stats:
        return battle_stats['error']
    
    user_data = response.json()
    # Extracting the raw stats
    current_stats = {
        'strength': user_data.get('strength', 0),
        'speed': user_data.get('speed', 0),
        'defense': user_data.get('defense', 0),
        'dexterity': user_data.get('dexterity', 0)
    }
    
    # Extracting modifiers
    strength_modifier = battle_stats.get('strength_modifier', 0)
    speed_modifier = battle_stats.get('speed_modifier', 0)
    dexterity_modifier = battle_stats.get('dexterity_modifier', 0)
    defense_modifier = battle_stats.get('defense_modifier', 0)

    # Extracting the stat info
    strength_info = battle_stats.get('strength_info', [])
    speed_info = battle_stats.get('speed_info', [])
    dexterity_info = battle_stats.get('dexterity_info', [])
    defense_info = battle_stats.get('defense_info', [])
    
    # Calculating modified stats
    modified_strength = round(current_stats['strength'] * (1 + strength_modifier / 100))
    modified_speed = round(current_stats['speed'] * (1 + speed_modifier / 100))
    modified_dexterity = round(current_stats['dexterity'] * (1 + dexterity_modifier / 100))
    modified_defense = round(current_stats['defense'] * (1 + defense_modifier / 100))
    
    link_text = f"Total Battle Stats for {discord_username}"
    profile_link = get_user_profile_link(torn_id, link_text)

    # Helper function to format modifier details
    def format_modifier_info(modifier, info):
        details = "\n".join(info)
        return f"{modifier}%\n{details}"

    # Formatting the output with commas and rounding
    output = (
        f"{profile_link}:\n\n"
        f"Base Battle Stats:\n\n"
        f"Strength: {current_stats['strength']:,}\n"
        f"Speed: {current_stats['speed']:,}\n"
        f"Dexterity: {current_stats['dexterity']:,}\n"
        f"Defense: {current_stats['defense']:,}\n\n"
        
        f"Effective Battle Stats:\n\n"
        f"Modified Strength: {modified_strength:,} ({strength_modifier}%)\n"
        f"Modified Speed: {modified_speed:,} ({speed_modifier}%)\n"
        f"Modified Dexterity: {modified_dexterity:,} ({dexterity_modifier}%)\n"
        f"Modified Defense: {modified_defense:,} ({defense_modifier}%)\n\n"

        f"Strength Modifier: {format_modifier_info(strength_modifier, strength_info)}\n\n"
        f"Speed Modifier: {format_modifier_info(speed_modifier, speed_info)}\n\n"
        f"Dexterity Modifier: {format_modifier_info(dexterity_modifier, dexterity_info)}\n\n"
        f"Defense Modifier: {format_modifier_info(defense_modifier, defense_info)}\n\n"
    )
    
    return output




def run_torn_commands():
    get_user_details()
