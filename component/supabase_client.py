from supabase import create_client, Client
import re  # Import the regular expressions module for sanitizing file names

# Define your Supabase URL and Key
SUPABASE_URL = 'https://bngznejumgjszdsmhmkk.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJuZ3puZWp1bWdqc3pkc21obWtrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjcwOTkyNTksImV4cCI6MjA0MjY3NTI1OX0.UG28yFZGV8-abqjpNdFwd-nczU0k1UDEB8sGAB6-dbo'

# Create a Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def sanitize_file_name(file_name):
    """
    Sanitize the file name by replacing spaces with underscores and removing special characters.
    """
    # Replace spaces with underscores and remove any non-alphanumeric characters except periods, underscores, and dashes
    sanitized_name = re.sub(r'[^a-zA-Z0-9._-]', '', file_name.replace(" ", "_"))
    return sanitized_name


def upload_file_to_supabase(bucket_name, file_content, file_name):
    """
    Uploads a file to the specified Supabase bucket and returns the public URL if successful.
    """
    try:
        # Sanitize the file name to ensure compatibility
        sanitized_file_name = sanitize_file_name(file_name)

        # Ensure the file path is within the 'edu_material' folder of the 'fyp' bucket
        file_path = f"edu_material/{sanitized_file_name}"  # This will place the file in the 'edu_material' folder

        # Upload the file to the specified bucket and folder
        response = supabase.storage.from_(bucket_name).upload(file_path, file_content)

        # Check if the response contains an error (for Supabase Python client, it should return a dictionary)
        if isinstance(response, dict) and response.get('error'):
            print(f"Error uploading file: {response['error']['message']}")
            return None

        # Construct the public URL for the uploaded file
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{file_path}"
        print(f"File uploaded successfully: {public_url}")
        return public_url

    except Exception as e:
        print(f"An error occurred during upload: {e}")
        return None
