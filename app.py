import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import openai
import time

# Set up OpenAI API key
openai.api_key = st.text_input("OpenAI API Key", type="password")

# Function to log in to LinkedIn
def login_to_linkedin(username, password):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode for better performance
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)  # Ensure you have ChromeDriver installed
    driver.get("https://www.linkedin.com/login")
    
    # Enter Username
    email_field = driver.find_element(By.ID, "username")
    email_field.send_keys(username)
    
    # Enter Password
    password_field = driver.find_element(By.ID, "password")
    password_field.send_keys(password)
    password_field.send_keys(Keys.RETURN)
    
    time.sleep(5)  # Wait for login to complete
    return driver

# Function to search for leads on LinkedIn
def search_leads(driver, search_query):
    search_box = driver.find_element(By.CSS_SELECTOR, "input.search-global-typeahead__input")
    search_box.send_keys(search_query)
    search_box.send_keys(Keys.RETURN)
    time.sleep(5)  # Wait for search results to load

# Function to scrape profile data
def scrape_profiles(driver, num_profiles=5):
    profiles = []
    profile_links = driver.find_elements(By.CSS_SELECTOR, "a.search-result__result-link")
    
    for link in profile_links[:num_profiles]:
        profile_url = link.get_attribute('href')
        driver.get(profile_url)
        time.sleep(3)  # Wait for profile to load
        
        try:
            name = driver.find_element(By.CSS_SELECTOR, "li.inline.t-24.t-black.t-normal").text
            title = driver.find_element(By.CSS_SELECTOR, "h2.mt1.t-18.t-black.t-normal.break-words").text
            company = driver.find_element(By.CSS_SELECTOR, "li.t-16.t-black.t-normal.inline-block").text
            profile_data = {
                'name': name,
                'title': title,
                'company': company,
                'profile_url': profile_url
            }
            profiles.append(profile_data)
        except Exception as e:
            st.error(f"Error scraping profile: {e}")
    
    return profiles

# Function to generate personalized message using OpenAI API
def generate_message(profile_data):
    prompt = f"Generate a personalized LinkedIn connection request for {profile_data['name']} who works as a {profile_data['title']} at {profile_data['company']}."
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=100
    )
    message = response.choices[0].text.strip()
    return message

# Function to send connection request
def send_connection_request(driver, profile_url, message):
    driver.get(profile_url)
    time.sleep(3)
    
    try:
        connect_button = driver.find_element(By.CSS_SELECTOR, "button.pv-s-profile-actions.pv-s-profile-actions--connect")
        connect_button.click()
        time.sleep(2)
        
        add_note_button = driver.find_element(By.CSS_SELECTOR, "button.mr1.artdeco-button.artdeco-button--muted.artdeco-button--2.artdeco-button--secondary")
        add_note_button.click()
        time.sleep(2)
        
        note_field = driver.find_element(By.CSS_SELECTOR, "textarea.send-invite__custom-message")
        note_field.send_keys(message)
        
        send_button = driver.find_element(By.CSS_SELECTOR, "button.ml1.artdeco-button.artdeco-button--3.artdeco-button--primary.ember-view")
        send_button.click()
        
        st.success(f"Connection request sent to {profile_data['name']}")
    except Exception as e:
        st.error(f"Failed to send connection request: {e}")

# Streamlit App Interface
st.title("LinkedIn Networking Automation Tool")

username = st.text_input("LinkedIn Username")
password = st.text_input("LinkedIn Password", type="password")
search_query = st.text_input("Search Query (e.g., 'Data Scientist in New York')")
num_profiles = st.slider("Number of Profiles to Scrape", 1, 20, 5)

if st.button("Start Networking"):
    if username and password and search_query:
        driver = login_to_linkedin(username, password)
        if driver:
            search_leads(driver, search_query)
            profiles = scrape_profiles(driver, num_profiles)
            
            for profile in profiles:
                st.write(f"Scraped Profile: {profile['name']} - {profile['title']} at {profile['company']}")
                message = generate_message(profile)
                st.write(f"Generated Message: {message}")
                send_connection_request(driver, profile['profile_url'], message)
            
            driver.quit()
        else:
            st.error("Failed to log in to LinkedIn")
    else:
        st.error("Please provide all required inputs")
