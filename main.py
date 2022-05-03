import requests
from requests.structures import CaseInsensitiveDict
from bs4 import BeautifulSoup
import pymongo

url = "https://adisinsight.springer.com/drugs/refine?isContentTypeSwitch=true"

headers = CaseInsensitiveDict()
headers["content-type"] = "application/x-www-form-urlencoded; charset=UTF-8"
headers["referer"] = "https://adisinsight.springer.com/search"


myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["XYZ"]
mycol = mydb["adisinsight"]
mycol.delete_many({})


def drug_finder():
    drug_name = str(input('Enter the name of drug : ')).strip().lower()
    data = "query=%7B%22baseQuery%22%3A%22drug-name%3A(" \
           f"%5C%22{drug_name}%5C%22)%22%2C%22facets%22%3A%7B%22drugs%22%3A%5B" \
           "%5D%2C%22deals%22%3A%5B%5D%2C%22drugSafety%22%3A%5B%5D%2C%22trials%22%3A%5B%5D%2C%22drugsArchive%22%3A%5B" \
           "%5D" \
           "%2C%22patents%22%3A%5B%5D%7D%2C%22sortBy%22%3A%7B%22drugSafety%22%3A%22%22%2C%22trials%22%3A%22%22%2C" \
           "%22deals" \
           "%22%3A%22%22%2C%22drugsArchive%22%3A%22%22%2C%22drugs%22%3A%22date%22%7D%7D&resultCount=1 "

    resp = requests.post(url, headers=headers, data=data)

    soup = BeautifulSoup(resp.content, 'html5lib')

    try:
        first_a = soup.find('a', class_='profile-link').attrs['href']
        first_url = f'https://adisinsight.springer.com/{first_a}'
    except AttributeError:
        first_url = 'No url found.'

    return first_url


def drug_detail_scraper(first_url):
    resp = requests.get(first_url)
    soup = BeautifulSoup(resp.content, 'html5lib')

    # top_part
    name = soup.find('h1', id='drugNameID').get_text().replace('\n', '').strip()
    try:
        alt_names = soup.find('span', class_='document__alt-name').get_text().replace('Alternative Names:', '').replace(
            '\n',
            '').strip()
    except:
        alt_names = ''
    try:
        price = soup.find('div', class_='profile_price').find_all('span')[-1].get_text().replace('\n', '').strip()
    except:
        price = ''

    # middle_part
    originator, developer, class_, moa, od_status, new_mol_entity, marketed, registered, prereg, phase3, phase2, phase1_2, phase1, preclinical = '', '', '', '', '', '', '', '', '', '', '', '', '', ''
    main_div = soup.find('div', class_='data-list data-list--properties-column')
    all_ul = main_div.find_all('ul', class_='data-list__content')

    main_ul = all_ul[:-1]

    main_list = []

    for ul in main_ul:
        single_ul_lis = ul.find_all('li', class_='data-list__property')
        for li in single_ul_lis:
            main_list.append(li)

    for datapoint in main_list:
        key = datapoint.find('strong', class_='data-list__property-key').get_text().replace('\n', '').replace('  ',
                                                                                                              '').strip()
        value = datapoint.find('span', class_='data-list__property-value').get_text().replace('\n', '').replace('  ',
                                                                                                                '').strip()
        if 'Originator' in key:
            originator = value
        elif 'Developer' in key:
            developer = value
        elif 'Class' in key:
            class_ = value
        elif 'Mechanism of Action' in key:
            moa = value
        elif 'Orphan Drug Status' in key:
            od_status = value
        elif 'New Molecular Entity' in key:
            new_mol_entity = value
        elif 'Marketed' in key:
            marketed = value.replace(';', ',')
        elif 'Registered' in key:
            registered = value
        elif 'Preregistration' in key:
            prereg = value
        elif 'Phase III' in key:
            phase3 = value
        elif 'Phase II' in key:
            phase2 = value
        elif 'Phase I/II' in key:
            phase1_2 = value
        elif 'Phase I' in key:
            phase1 = value
        elif 'Preclinical' in key:
            preclinical = value

    # bottom_part
    mre_dict = {}
    mre = all_ul[-1].find_all('li', class_='data-list__property')

    for datapoint in mre:
        key = datapoint.find('strong', class_='data-list__property-key').get_text().replace('\n', '').replace('  ',
                                                                                                              '').strip()
        value = datapoint.find('span', class_='data-list__property-value').get_text().replace('\n', '').replace('  ',
                                                                                                                '').strip()
        if key in mre_dict:
            key = key + '_'
        mre_dict[key] = value

    most_recent = str(mre_dict).strip('{}')
    if len(mre_dict) == 0:
        most_recent = ''

    drug_data_dict = {'Name': name, 'Alternative Names': alt_names, 'Price': price, 'Originator': originator, 'Developer': developer, 'Class': class_, 'Mechanism of action': moa, 'Orphan Drug Status': od_status, 'New Molecular Entity': new_mol_entity, 'Marketed': marketed, 'Registered': registered, 'Preregisteration': prereg, 'Phase 3': phase3, 'Phase 2': phase2, 'Phase 1/2': phase1_2, 'Phase 1': phase1, 'Preclinical': preclinical, 'Most Recent': most_recent}
    
    mycol.insert_one(drug_data_dict)



drug_detail_scraper(drug_finder())
