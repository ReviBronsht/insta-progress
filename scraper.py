#imports
import time
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import json
import os
import pandas as pd
import time
from moviepy.editor import VideoFileClip
import urllib.request

#setting up selenium
options = Options()
prefs = {"profile.managed_default_content_settings.images": 2}
options.add_experimental_option("prefs", prefs)
PATH = "C:\\Users\\revib\\Desktop\\Python_test\\chromedriver2\\chromedriver.exe"
s = Service(PATH)
driver =  webdriver.Chrome(service=s, options=options)
wait = WebDriverWait(driver, 15)

#setting functions to find one element and many elements with try, except and wait
def find_one(driver, wait, by, query, what):
    try:
        return wait.until(EC.presence_of_element_located((by, query)))
    except Exception as e:
        print("Unable to find " + what)
        return None
def find_many(driver, wait, by, query, what):
    try:
        return wait.until(EC.presence_of_all_elements_located((by, query)))
    except Exception as e:
        print("Unable to find " + what)
        return None

reels = [] #all reels list
error_list = [] #list to save errors

profile_link = "https://www.instagram.com/navy.bird.art/reels/"

driver.get(profile_link)

#get links to needed reels by scrolling down profile and getting reels until max reel amount reached
reels_links = []
max_reels = 10
prev_amount = 0

while len(reels_links) < max_reels:
    #wait for page load & scroll to bottom
    time.sleep(5) 
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    
    #instagram prompts to login, if prompt exists, closes it
    closebtn = find_one(driver, wait, By.XPATH, "//*/div[@class='x6s0dn4 x78zum5 xdt5ytf xl56j7k']", "closebtn")
    if closebtn:
        closebtn.click()
        
    #gets links by xpath and appends new links that are reel inks into links array
    links = find_many(driver, wait, By.XPATH, "//*/a[@class='x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz _a6hd']", "reels links")
    if links:
        for idx,l in enumerate(links):
            curr_l = l.get_attribute("href")
            if curr_l not in reels_links and "reel" in curr_l:
                reels_links.append(curr_l)
    
    print(reels_links)
    print(len(reels_links))
    
    # if can't get new links, then scrolled to maximum. breaks out of loop
    if prev_amount == len(links):
        break
    else:
        prev_amount = len(links)
    

for i, reel_link in enumerate(reels_links):
    print(reel_link)
    print(i , "/" , len(reels_links))
    #reel_link = "https://www.instagram.com/navy.bird.art/reel/C7mr6wPK9sO/" #get reel link

    try: 
        reel = {'link':reel_link} #saving single reel
        
        #getting reel id from link
        split_link = reel_link.split("/")
        reel["id"] = split_link[4]
        
        #getting creator from link
        split_link = profile_link.split("/")
        reel["creator"]=split_link[3]
        
        #get link for report
        driver.get(reel_link)
        
        #get reel video link by xpath
        video = find_one(driver, wait, By.XPATH, "//*/video[@class='x1lliihq x5yr21d xh8yej3']", "video")
        video = video.get_attribute("src")
        reel["video_link"] = video
        
        #getting video length by downloading video with urllib request and getting duration with moviepy
        urllib.request.urlretrieve(video, 'videoname.mp4')
        clip = VideoFileClip("videoname.mp4")
        reel["video_duration"] = clip.duration 
        
        #get reel cover image link by xpath
        image = find_one(driver, wait, By.XPATH, "//*/img[@class='x5yr21d xl1xv1r xh8yej3']", "image")
        image = image.get_attribute("src")
        reel["cover_image_link"] = image
        
        #getting caption by xpath
        caption = find_one(driver, wait, By.XPATH, "//*/h1[@class='_ap3a _aaco _aacu _aacx _aad7 _aade']", "caption")
        reel["caption"] = caption.get_attribute("textContent")
        
        #getting tags by xpath and removing tags from caption
        tags_txt = []
        tags = find_many(driver, wait, By.XPATH, "//*/h1[@class='_ap3a _aaco _aacu _aacx _aad7 _aade']/a", "tags")
        if tags:
            for idx,tag in enumerate(tags):
                tags_txt.append(tag.text)
        reel["tags"] = tags_txt
        tags_txt = sorted(tags_txt,key=len,reverse=True)
        for tag in tags_txt:
            reel["caption"] =  reel["caption"].replace(tag,"")
        
        #getting number of tags
        reel["num_of_tags"] = len(tags)
        
        #getting audio by xpath
        audio = find_one(driver, wait, By.XPATH, "//*/span[@class='x6ikm8r x10wlt62 xlyipyv xuxw1ft']", "audio")
        reel["audio"] = audio.get_attribute("textContent")
        
        #getting likes and comments by xpath and seperating to likes and comments
        likes_comments = find_one(driver, wait, By.XPATH, "//*/meta[@name='description']", "likes_comments")
        likes_comments = likes_comments.get_attribute("content")
        likes_comments = likes_comments.split(" ")
        reel["likes"] = likes_comments[0]
        reel["comments"] = likes_comments[2]
        
        #getting timestamp by xpath
        timestamp = find_one(driver, wait, By.XPATH, "//*/time[@class='x1p4m5qa']", "timestamp")
        reel["timestamp"] = timestamp.get_attribute("datetime")
        
        
        #append reel to all reels
        print(reel)
        reels.append(reel)
    except Exception as e:
        print("unable to get report", e)
        err_log = {"source": reel_link,"error":e,"traceback":str(traceback.format_exc())}
        error_list.append(err_log)
        


#saving reels to excel
#list of dictionaries of data to df
df = pd.DataFrame(reels)
#save to excel
excel_file_path = "reels.xlsx"
df.to_excel(excel_file_path, index=False)

#saving errors to excel
#list of dictionaries of data to df
err_df = pd.DataFrame(error_list)
#save to excel
excel_file_path = "error_list.xlsx"
err_df.to_excel(excel_file_path, index=False)

driver.close()


