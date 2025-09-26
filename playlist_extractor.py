import plistlib
import os
import re
from urllib.parse import unquote
import datetime

def sanitize_filename(name):
    """
    Removes characters that are invalid for filenames.
    """
    return re.sub(r'[\\/*?:"<>|]', "", name)

def get_track_property(track_data, key, default=''):
    """
    Safely gets a property from the track data dictionary.
    Converts values to string and handles special cases.
    """
    value = track_data.get(key, default)

    # Convert milliseconds to seconds for 'Time'
    if key == 'Total Time' and isinstance(value, int):
        return str(value // 1000)

    # Format datetime objects
    if isinstance(value, datetime.datetime):
        return value.strftime('%d/%m/%Y, %H:%M')
    
    # Decode file path URI for 'Location'
    if key == 'Location' and isinstance(value, str):
        # Remove 'file://' prefix and decode URL-encoded characters
        path = unquote(value).replace('file://', '')
        # iTunes on Mac uses 'Macintosh HD' as a prefix which might not
        # be the actual start of the path for other systems.
        # This part might need adjustment based on the OS.
        if path.startswith('/Users/'):
            # For Mac users
            return 'Macintosh HD' + path
        return path


    return str(value) if value is not None else ''

def extract_playlists_from_library(xml_path, output_dir='playlists'):
    """
    Parses an iTunes XML library file and extracts all playlists into
    separate tab-separated text files.

    Args:
        xml_path (str): The path to the Library.xml file.
        output_dir (str): The name of the directory to save playlist files.
    """
    print(f"Attempting to load library file from: {xml_path}")
    try:
        with open(xml_path, 'rb') as f:
            library = plistlib.load(f)
    except FileNotFoundError:
        print(f"Error: The file '{xml_path}' was not found.")
        return
    except Exception as e:
        print(f"Error: Failed to parse the XML file. {e}")
        return

    tracks = library.get('Tracks', {})
    playlists = library.get('Playlists', [])

    if not tracks:
        print("Warning: No tracks found in the library file.")
    if not playlists:
        print("Warning: No playlists found in the library file.")
        return

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    print(f"Saving playlists to '{output_dir}/' directory...")

    # Define the header and the corresponding keys in the XML
    # This mapping is based on the provided "All Drum and Bass.txt" example
    header_map = {
        "Name": "Name",
        "Artist": "Artist",
        "Composer": "Composer",
        "Album": "Album",
        "Grouping": "Grouping",
        "Work": "Work",
        "Movement Number": "Movement Number",
        "Movement Count": "Movement Count",
        "Movement Name": "Movement Name",
        "Genre": "Genre",
        "Size": "Size",
        "Time": "Total Time", # Note: XML key is 'Total Time'
        "Disc Number": "Disc Number",
        "Disc Count": "Disc Count",
        "Track Number": "Track Number",
        "Track Count": "Track Count",
        "Year": "Year",
        "Date Modified": "Date Modified",
        "Date Added": "Date Added",
        "Bit Rate": "Bit Rate",
        "Sample Rate": "Sample Rate",
        "Volume Adjustment": "Volume Adjustment",
        "Kind": "Kind",
        "Equaliser": "Equalizer",
        "Comments": "Comments",
        "Plays": "Play Count",
        "Last Played": "Play Date UTC",
        "Skips": "Skip Count",
        "Last Skipped": "Skip Date",
        "My Rating": "Rating",
        "Location": "Location"
    }
    
    header = list(header_map.keys())
    xml_keys = list(header_map.values())

    playlist_count = 0
    for playlist in playlists:
        playlist_name = playlist.get('Name')
        playlist_items = playlist.get('Playlist Items', [])

        if not playlist_name or not playlist_items:
            continue
        
        # Don't export special playlists like "Library" or "Music"
        if playlist.get('Master') or playlist.get('Music'):
            continue

        sanitized_name = sanitize_filename(playlist_name)
        output_filepath = os.path.join(output_dir, f"{sanitized_name}.txt")

        print(f"  - Extracting playlist: '{playlist_name}' ({len(playlist_items)} tracks)")

        with open(output_filepath, 'w', encoding='utf-8', newline='') as f:
            # Write header
            f.write('\t'.join(header) + '\n')

            # Write track data
            for item in playlist_items:
                track_id = str(item.get('Track ID'))
                track_data = tracks.get(track_id)

                if track_data:
                    row_data = [get_track_property(track_data, key) for key in xml_keys]
                    f.write('\t'.join(row_data) + '\n')
        
        playlist_count += 1
    
    print(f"\nExtraction complete. Exported {playlist_count} playlists.")

if __name__ == '__main__':
    # The script will look for 'Library.xml' in the same directory it is run from.
    # You can change this to a full path if your file is elsewhere.
    itunes_xml_file = 'Library.xml'
    extract_playlists_from_library(itunes_xml_file)
