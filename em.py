import streamlit as st
from docx import Document
from io import StringIO
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
import seaborn as sns
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.proxy import Proxy, ProxyType
import time
import logging
import os
import pandas as pd
import plotly.express as px
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
import plotly.express as px
class LinkedInBot:
    def __init__(self, delay=5):
        if not os.path.exists("data"):
            os.makedirs("data")
        log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(level=logging.INFO, format=log_fmt)
        self.delay = delay
        logging.info("Starting driver")
        # # Create a webdriver instance
        self.driver = webdriver.Edge()

    def login(self, email, password):
        """Go to LinkedIn and login"""
        logging.info("Logging in")
        self.driver.maximize_window()
        self.driver.get('https://www.linkedin.com/login')
        time.sleep(self.delay)

        self.driver.find_element(By.ID, 'username').send_keys(email)
        self.driver.find_element(By.ID, 'password').send_keys(password)

        self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(self.delay)


    def search_linkedin(self, company):
        """Enter keywords into the search bar"""
        logging.info("DA of Company Employee")
        self.driver.get("https://www.linkedin.com/jobs/")
        # Search based on keywords, location, and date posted and hit enter
        self.driver.get(f"https://www.linkedin.com/company/{company}/people")
        logging.info("Keyword search successful")
        time.sleep(self.delay)

    def search_em(self):
        """Enter keywords into the search bar"""
        em_df=pd.DataFrame(columns=['Name', 'Current', 'Position', 'Highest Education', 'Education 2'])
        full_em=False
        em_li=[]
        while True:
            em_list=self.driver.find_elements(By.XPATH, ".//img[contains(@alt, 'profile picture')]")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.wait()
            em_list1=self.driver.find_elements(By.XPATH, ".//img[contains(@alt, 'profile picture')]")
            if (len(em_list1)==len(em_list)):
                break

        elems=self.driver.find_elements(By.XPATH,"//div[@class='ember-view lt-line-clamp lt-line-clamp--single-line org-people-profile-card__profile-title t-black']")   
        elems_curr_pos=self.driver.find_elements(By.XPATH,"//div[@class='ember-view lt-line-clamp lt-line-clamp--multi-line']")   
        em_names = [element.text for element in elems]
        em__curr_pos = [element.text for element in elems_curr_pos]

        em_list=self.driver.find_elements(By.XPATH, ".//img[contains(@alt, 'profile picture')]")
        data = []

        for em, name, curr_position in zip(em_list, em_names, em__curr_pos):
            try:
                ActionChains(self.driver) \
                    .key_down(Keys.CONTROL) \
                    .click(em) \
                    .key_up(Keys.CONTROL) \
                    .perform()
                # Switch to the newly opened tabs one by one
                original_window = self.driver.current_window_handle
                for handle in self.driver.window_handles:
                    if handle != original_window:
                        self.driver.switch_to.window(handle)
                        time.sleep(2)
                        
                        # Getting the work history and education history
                        education_hist = self.driver.find_elements(By.XPATH, "//*[contains(@class,'XKPXojatUzPiUYuBkoClDWsYSHGcmSZTZkY') and .//*[text()='Education']]/following-sibling::div")

                        for education_section in education_hist:
                            education_list = education_section.find_elements(By.XPATH, ".//*[contains(@class, 'display-flex flex-row justify-space-between')]")
                            for ed_ex in education_list:
                                # Create a list with a fixed number of elements, padded with None if necessary
                                if len(ed_ex.text.split('\n')) == 1:
                                    row = [name, curr_position, ed_ex.text, None]
                                else:
                                    row = [name, curr_position] + ed_ex.text.split('\n')[:2]  # only take the first 2 lines if there are more

                                # Ensure the row has exactly 4 elements
                                while len(row) < 4:
                                    row.append(None)
                                data.append(row)
                        
                        self.driver.close()
                        self.driver.switch_to.window(original_window)
            except Exception as e:
                print(f"Error processing element: {e}")
                continue
        # Create DataFrame
        columns = ["Name", "Current Position", "Highest Education", "Education 2"]
        em_df = pd.DataFrame(data, columns=columns)

        # Merge rows for repeating names
        merged_data = {}
        for _, row in em_df.iterrows():
            key = (row['Name'], row['Current Position'])
            if key not in merged_data:
                merged_data[key] = [row['Highest Education'], row['Education 2']]
            else:
                if merged_data[key][1] is None:
                    merged_data[key][1] = row['Highest Education']
                elif row['Highest Education'] not in merged_data[key]:
                    merged_data[key].append(row['Highest Education'])

        # Prepare final data for DataFrame
        final_data = []
        for (name, curr_position), education in merged_data.items():
            # Ensure the list has exactly 3 elements: Highest Education, Education 2, None
            while len(education) < 3:
                education.append(None)
            final_data.append([name, curr_position] + education[:2])
            
        # # Create DataFrame
        columns = ["Name", "Current Position", "Highest Education", "Education 2"]
        em_df = pd.DataFrame(final_data, columns=columns)
        # # Remove duplicate rows
        em_df.drop_duplicates(inplace=True)
        if em_df['Highest Education'].equals(em_df['Education 2']):
            em_df = em_df.drop(columns=['Education 2'])
        # Save DataFrame to CSV
        em_df.to_csv('employee_data.csv', index=False)
        st.write(em_df)
        # EDA - Plotting
        fig = px.bar(em_df['Highest Education'].value_counts().reset_index().rename(columns={'index': 'Highest Education', 'Highest Education': 'Count'}),
                    y='Count', x='Highest Education', orientation='v', title='Education Distribution of EMPS')

        # Display the plot in Streamlit
        st.plotly_chart(fig)



    def wait(self, t_delay=None):
        """Just easier to build this in here."""
        delay = self.delay if t_delay is None else t_delay
        time.sleep(delay)


    def close_session(self):
        """Close the actual session"""
        logging.info("Closing session")
        self.driver.close()

    def run(self, email, password, company):
        self.login(email=email, password=password)
        self.wait()
        logging.info("Begin LinkedIn keyword search")
        self.search_linkedin(company)
        self.wait()
        self.search_em()
        self.wait()
        self.close_session()

def main():
    st.set_page_config(layout="wide") 
    st.title("Where do Companies hire from?? ")

    # Scrape LinkedIn Jobs
    st.header("Company Personnel DA & DE")
    st.write("Enter your LinkedIn credentials and search criteria below to get poster Company Data  .")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    company = st.text_input("company")


    if st.button("Scrape People"):
        bot = LinkedInBot()
        bot.run(email, password, company)
        st.success("People scraping completed!")


if __name__ == "__main__":
    main()
