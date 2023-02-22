#!/usr/bin/env python
# coding: utf-8

# In[1130]:


from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import requests
import re
import numpy as np
import pandas as pd
import time


# In[1144]:


#Set q1 answer function
def q1_answer():
    try:
        #Employ scraping function
        ebay_df=ebay_scrape()
        #read scraped data to csv
        ebay_df.to_csv("ebay_df.csv")
        #Print out the percentage of undervalued cards
        print("The proportion of overvalued amazon cards was:", np.round(sum(ebay_df['net_cost']>0)/len(ebay_df['net_cost']),3))
    except:
        print("Error with the connection...")


# In[1145]:


#create function to scrape ebay
def ebay_scrape():
    #Create temporary df to store all the information
    temp_df=pd.DataFrame()
    #Create df to update on every iteration
    ebay_df=pd.DataFrame()
    for i in range(1,11):
        #Set url
        url="https://www.ebay.com/sch/i.html?_nkw=amazon+gift+card&LH_Sold=1&_pgn="+str(i)
        #set header
        hdr = {'User-Agent': 'Mozilla/5.0'}
        #open url and parse result 
        page = requests.get(url, headers=hdr)
        soup = BeautifulSoup(page.content, 'html.parser')
        #Write page to html file
        with open("ebay_amazon_page"+"_"+str(i)+".html", "w", encoding = 'utf-8') as file:
                    # prettify the soup object and convert it into a string  
                file.write(str(soup))
        #Pause loop to not get blocked
        time.sleep(10)
        #Read file into python
        htmlfile=open("ebay_amazon_page"+"_"+str(i)+".html", "r").read()
        #Convert to soup object
        soup=BeautifulSoup(htmlfile, 'lxml')
        #Find all the listings objects
        listings = soup.find_all('li', attrs={'class': 's-item'})
        #Create object to store the listing name
        prod_name=[]
        #Create object to store the price
        prod_price=[]
        #Create object to store the shipping cost
        prod_shipping=[]
        #List through listings objects
        for listing in listings:
            #Loop through item title objects
            for name in listing.find_all('div', attrs={'class':"s-item__title"}):
                #Get rid of first invalid header
                if name.text!="Shop on eBay":
                    #Try to append shipping cost
                    try:
                        prod_shipping.append(listing.find('span',attrs={"class":"s-item__shipping s-item__logisticsCost"}).text)
                    #For objects with no listed shipping cost, append 0 to list
                    except:
                        prod_shipping.append("0")
                    #Find product name
                    prod_name.append(re.sub(r"New Listing","",name.text))
                    #Find product price
                    price=listing.find('span', attrs={'class':"s-item__price"}).text
                    #append price to price list
                    prod_price.append(price)
        #Clean the shipping cost
        prod_shipping=clean_shipping(prod_shipping)
        #subset to only numbers that begin with a digit between 1 and 3 digits long, followed by a decimal, followed by two digits
        #Apply function to find the price in the description
        list_price_description= generate_description__price(prod_name)
        #combine all these lists into pandas df
        temp_df=pd.DataFrame(
                {'product_name': prod_name,
                 "listed_price_description":list_price_description,
                 #NOTE:change back to prod_price_clean
                 'product_listed_price': prod_price,
                 'product_shipping':prod_shipping
                })
        #remove cards with a range of values
        temp_df=temp_df[temp_df["product_listed_price"].str.contains("to")==False]
        #remove $ and convert to float
        temp_df['product_listed_price']=[float(re.sub(r"\$","",i)) for i in temp_df['product_listed_price']]
        #Combine the temp_df with the final df every iteration
        ebay_df=pd.concat([ebay_df, temp_df])
        #Compute net cost as listed price+shipping-price in the description
        ebay_df["net_cost"]=(ebay_df['product_listed_price']+ebay_df['product_shipping'])-ebay_df['listed_price_description']
    #Return the final df
    return ebay_df


# In[1146]:


#Function to clean shipping cost
def clean_shipping(prod_shipping):
    #Loop through all product shipping values
    for i in range(0, len(prod_shipping)):
        #Try to find any digits in the description using regex
        try:
            prod_shipping[i]=re.findall(r"\d\.\d+", prod_shipping[i])[0]
        except:
            #if there are no numbers, then it is likely a "Free shipping" value which we will just append to our list
            prod_shipping[i]=prod_shipping[i]
    #Replace the "Free shipping" tag with 0
    prod_shipping=[float(i.replace('Free shipping','0')) for i in prod_shipping]
    return prod_shipping


# In[1147]:


def generate_description__price(prod_name): 
    list_price_description=[]
    for i in range(0, len(prod_name)):
        try:
            #Find if the description contains any dollar values
            price_dirty=re.findall(r'\$\d+',prod_name[i])[0]
            #Remove $ signs
            price_clean=re.sub(r"\$","",price_dirty)
            #Append cleaned price
            list_price_description.append(price_clean)
        #add exception where there is no $ sign
        except IndexError:
            #search string for a number followed by the word 'Dollars' and strip all strings
            try:
                list_price_description.append(re.sub(' [A-Za-z]+.','',re.findall(r'.\d Dollars',prod_name[i])[0]))
                #Add exception for if there is neither a $ nor the word "Dollars"
            except IndexError:
                #Search string for a number followed by "USD" and then strip away "USD"
                try:
                    list_price_description.append(re.sub(' [A-Za-z]+.','',re.findall(r'.\d USD',prod_name[i])[0]))
                    #Add exception if the string contains none of these to append NA
                except IndexError:
                    #Add exception to account for edge cases and append NA
                    list_price_description.append(np.nan) 
    #Replace values with float
    list_price_description=[float(i) for i in list_price_description]
    #Return the list
    return list_price_description


# In[1148]:


if __name__ == '__main__':
    q1_answer()
    ebay_df=pd.read_csv("ebay_df.csv")


# In[1136]:


#Check proportion of NA's to ensure that ~90% of prices in the description were detected
print("The proportion of NA values is",np.round(sum(ebay_df['net_cost'].isna())/len(ebay_df['net_cost']),2))
#Check porportion of undervalued amazon cards
print("The proportion of undervalued amazon cards is", np.round(sum(ebay_df['net_cost']<0)/len(ebay_df['net_cost']),3))
#Check proportion of perfectly valued amazon gift cards
print("The proportion of perfectly valued amazon cards is",  np.round(sum(ebay_df['net_cost']==0)/len(ebay_df['net_cost']),3))


# In[1139]:


#View values of scraped df
pd.set_option('display.max_rows', 600)
#write output to .txt
with open('screen_JakeBrophy.txt', 'w') as f:
    f.write(str(ebay_df[ebay_df['net_cost']>0]))
#Write the entire df to a .txt
with open('screen_q1_JakeBrophy_total.txt', 'w') as f:
    f.write(str(ebay_df))
#Display values with a net cost greater than 0
ebay_df[ebay_df['net_cost']>0]


# There are a few possible reasons for cards selling above face value:
# 
# 1. People do not pay attention to the shipping cost and then buy cards that appear to be undervalued but are actually overvalued including the shipping cost
# 2. Amazon does not accept PayPal, but ebay does. For people with a Paypal balance who want to spend this paypal money on Amazon, converting these paypal dollars into something usable on Amazon is only doable by going through Ebay, which increases demand and drives up the price. Additionally, it is impossible to buy anything from Amazon overseas without a credit card, and for those who don't want to use a credit card but have paypal, buying an amazon gift card on ebay with a paypal account is the only way to purchase an item on Amazon.
# 3. It's part of a fraud or money laundering scheme where people will launder stolen credit cards which are easy to track to a gift card that is much less easy to track and is usable as tangible money. Paying more for a gift card than its worth is easy if its not the scammer's own money being spent. This isn't the case with most of these, but there is an example where a 10 dollar gift card sold for 500 dollars and a few other cases that appear to be fraud.

# In[1149]:


def q2_answer():
    #Try the fctables login url
    try:
        url="https://www.fctables.com/user/login/"
        #Open the page and read the contents
        page=requests.get(url)
        webpage=BeautifulSoup(page.content, 'html.parser')
        #Reques session
        session_requests=requests.session()
        #set headers
        HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36', 
                   'Request URL': url}
        #Create post request
        res = session_requests.post(url, 
                                        data = {"login_action" : "1",
                                              "login_username" : "jakebrophy68@gmail.com",
                                              "login_password" : "jakebrophy", 
                                              "user_remeber" : "1", 
                                              "submit" : "1"},
                                        headers = HEADERS,
                                        timeout = 15)
        #get login cookies
        cookies = session_requests.cookies.get_dict()
        #Open betting url and read contents
        URL2="https://www.fctables.com/tipster/my_bets/"
        page2 = session_requests.get(URL2, cookies=cookies)
        doc2 = BeautifulSoup(page2.content, 'html.parser')
        #Check whether Wolfsburg shows up in the site
        if "Wolfsburg" in doc2.text:
            print("Wolfsburg is present in the site and the login was successful!")
    except:
        print("Error with login...")
if __name__ == '__main__':
      q2_answer()


# In[ ]:




