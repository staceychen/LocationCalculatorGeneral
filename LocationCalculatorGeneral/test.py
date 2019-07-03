#import requests
import formulas
import csv
import requests

def get_focal_point(location_list, r1):
    
    # get lat and long for each address
    '''
    for address in address_list:
        response = requests.get("http://dev.virtualearth.net/REST/v1/Locations/" + address,
                            params={"include":"queryParse",
                            "key":"AvQOaBs2cYn6OAWmZ9tEAvGuJGfJusGnLSyHnD9g7USe35x69PmSiyk_51Htk3Z0"})
        data = response.json()
        lat = data['resourceSets'][0]['resources'][0]['point']['coordinates'][0]
        lng = data['resourceSets'][0]['resources'][0]['point']['coordinates'][1]
        
        # add to location_list
        location_list.append(address, lat, lng)

        print(str(lat) + ", " + str(lng))
    '''
    #list of location set around every point in tuple form (location, set)
    local_set_list =[]
    # iterate through location_list to create sets for each location
    for location in location_list:
        lat1 = location[0]
        lon1 = location[1]
        local_set = set()
        for other_location in location_list:
            lat2 = other_location[0]
            lon2 = other_location[1]
            dist = formulas.haversine(lat1, lon1, lat2, lon2)
            if dist <= float(r1):
                local_set.add(other_location)
        local_set_list.append((location, local_set))
    
    #local set around focal point of locations in (address, lat, long)
    local_set = set()
    # focal point
    focal_point = None
    #iterate through dictionary to get largest set and focal point
    for loc, self_set in local_set_list:
        if (len(self_set) > len(local_set)):
            local_set = self_set
            focal_point = loc
    
    return (focal_point, local_set)

def create_remote_set(focal_point, location_list, r2):
    #remote set around focal point of locations in (address, lat, long)
    remote_set = set()

    lat1 = focal_point[0]
    lon1 = focal_point[1]
    for loc in location_list:
        lat2 = loc[0]
        lon2 = loc[1]
        dist = formulas.haversine(lat1, lon1, lat2, lon2)
        if dist > float(r2):
            remote_set.add(loc)
    return remote_set

def generate_geo_relationship(country1, other_center):
    #this is for using the bing reverse geocode api
    coord2 = str(other_center[0]) +","+ str(other_center[1])
    response2 = requests.get("http://dev.virtualearth.net/REST/v1/Locations/" + coord2,
                params={"key":"AjhzSUKjNFFV0ckKVCV64tSLhw_EWSlN6LP9UPiWdEJDRMZn3Vm17HtoSclZZfO_ ",
                        })
    data2 = response2.json()
    #get the country data
        
    try:
        country2 = str(data2['resourceSets'][0]['resources'][0]['address']['countryRegion'])
    except:
        country2 = "N/A"
      
    if country1 == country2:
        if country1 == "N/A":
            return (country1, country2, "N/A")
        else: 
            return (country1, country2, "domestic")
    else:
        return (country1, country2, "cross border")

    
def output_each_patent(ungrouped, patent, r1, r2):
    #get the local locations
    (local_center, local_set) = get_focal_point(ungrouped, r1)
    #get the remote locations
    remote_set = create_remote_set(local_center, ungrouped, r2)
    #find the locations that are not local and not remote
    inbetween = set(ungrouped) - remote_set - local_set
    
    #row to write
    row = []
    row.append(patent)
    row.append(len(ungrouped))
    row.append(len(local_set))
    row.append(len(remote_set))
    
        
    # get local country
    coord1 = str(local_center[0]) +","+ str(local_center[1])
    response1 = requests.get("http://dev.virtualearth.net/REST/v1/Locations/" + coord1,
                params={"key":"AjhzSUKjNFFV0ckKVCV64tSLhw_EWSlN6LP9UPiWdEJDRMZn3Vm17HtoSclZZfO_ ",
                        })
    data1 = response1.json()
    #get the country data
    try:
        country1 = str(data1['resourceSets'][0]['resources'][0]['address']['countryRegion'])
    except:
        country1 = "N/A"
        
    
    #list of sets of remote groups
    remote_groups = []
    
    while len(remote_set) > 0:
        #get largest remote group, add to remote groups and remove from set of ungrouped remotes
        remote_group = get_focal_point(remote_set, r1)
        remote_groups.append(remote_group)
        remote_set -= remote_group[1]
        
    row.append(1 + len(remote_groups)) # number of clusters
    row.append(r1) # local radius
    row.append(r2) # remote radius
    with open('outputs/output.csv', 'a', newline="\n", encoding='latin-1') as out_file: 
        csv_writer = csv.writer(out_file, delimiter=',')
        '''
        header = ["patent_id", "number_of_inventors", "number_of_local_inventors", "number_of_remote_inventors", "number_of_clusters (local+remote)", "radius_local", 
                  "radius_remote", "local_cluster", "nonlocal_cluster", "remote_cluster"]
        csv_writer.writerow(header)
        '''
        # header = ["group_classification", "locations", "point_lat", "point_lng", "country", "geographical_relationship", "haversine_distance_to_local"]
        
        
        # convert local_set from a set of tuples to a list of strings
        local_set_string = []
        for (lat, lon, id) in local_set:
            coord = '(' + str(lat) + ',' + str(lon) +')'
            local_set_string.append(coord)
        # dict for local_cluster
        local_cluster_dict = {'number_of_inventors_in_cluster': len(local_set),
                              'locations': '; '.join(local_set_string),
                              'center_lat': local_center[0],
                              'center_lng': local_center[1],
                              'country': country1,
                              'geographical_relationship:': 'domestic',
                              'haversine_distance_to_local': 'N/A'}
        row.append(local_cluster_dict)
        
        # convert inbetween set from a set of tuples to a list of strings
        inbetween_set_string = []
        for (lat, lon, id) in inbetween:
            coord = '(' + str(lat) + ',' + str(lon) +')'
            inbetween_set_string.append(coord)
        
        # dict for nonlocal_cluster
        nonlocal_cluster_dict = {'number_of_inventors_in_cluster': len(inbetween),
                              'locations': '; '.join(inbetween_set_string),
                              'center_lat': 'N/A',
                              'center_lng': 'N/A',
                              'country': 'N/A',
                              'geographical_relationship:': 'N/A',
                              'haversine_distance_to_local': 'N/A'}
        row.append(nonlocal_cluster_dict)
        
        
        # sort remote groups by distance away from local focal point
        remote_group_list = []
        for remote_group in remote_groups:
            (coordinates, group) = remote_group
            dist = formulas.haversine(local_center[0], local_center[1], coordinates[0], coordinates[1])
            remote_group_list.append((coordinates, group, dist))
            remote_group_list.sort(key=lambda tup: tup[2])  # sorts in place
        
        for remote_group in remote_group_list:
            (coordinates, group, dist) = remote_group
            # convert remote_group from a set of tuples to a list of strings
            remote_group_string = []
            for (lat, lon, id) in group:
                coord = '(' + str(lat) + ',' + str(lon) +')'
                remote_group_string.append(coord)
            (c1, c2, rel) = generate_geo_relationship(country1, coordinates)
            # dict for remote_cluster
            remote_cluster_dict = {'number_of_inventors_in_cluster': len(group),
                                  'locations': '; '.join(remote_group_string),
                                  'center_lat': coordinates[0],
                                  'center_lng': coordinates[1],
                                  'country': c2,
                                  'geographical_relationship:': rel,
                                  'haversine_distance_to_local': formulas.haversine(local_center[0], local_center[1], coordinates[0], coordinates[1])}
            row.append(remote_cluster_dict)
        csv_writer.writerow(row)
        
if __name__ == '__main__':
    
    # write header
    with open('outputs/output.csv', 'w', newline="\n", encoding='latin-1') as out_file: 
        csv_writer = csv.writer(out_file, delimiter=',')
        header = ["patent_id", "number_of_inventors", "number_of_local_inventors", "number_of_remote_inventors", "number_of_clusters (local+remote)", "radius_local", 
                  "radius_remote", "local_cluster", "nonlocal_cluster", "remote_cluster"]
        csv_writer.writerow(header)
    # process radii
    r1 = 0
    r2 = 0
    
    with open('inputs/arguments.csv', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        
        #create the list of ungrouped addresses
        for row in reader:
            r1 = row['r1']
            r2 = row['r2']
            
    # process patent records
    with open('inputs/input100_blank.csv', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        
        #create the set of ungrouped addresses
        ungrouped = []
        total_length =  sum(1 for row in reader)
       
        
        
        for row in reader:
            if (reader.line_num == 1):
                patent = row['patent_id']
                lat = row['inventor_add_lat']
                lng = row['inventor_add_lon']
                inventor_id = row['inventor_id']
                ungrouped.append((lat, lng, inventor_id))
            elif (reader.line_num == total_length):
                #process last row here
                if row['patent_id'] == patent: 
                    try:
                        patent = row['patent_id']
                        lat = row['inventor_add_lat']
                        lng = row['inventor_add_lon']
                        inventor_id = row['inventor_id']
                        ungrouped.append((lat, lng, inventor_id))
                        
                        print(row)
                        output_each_patent(ungrouped, patent, r1, r2)
                    except ValueError:
                        print(ValueError)
                        print(int(row['inventor_add_lat'][0]))
                        print(row['inventor_add_lon'])
                        print(type(lng))
                    
                else:
                    
                    patent = row['patent_id']
                    ungrouped = []
                    lat = row['inventor_add_lat']
                    lng = row['inventor_add_lon']
                    inventor_id = row['inventor_id']
                    ungrouped.append((lat, lng, inventor_id))
                    output_each_patent(ungrouped, patent, r1, r2)
             
            else:      
                if row['patent_id'] == patent:
                    
                        patent = row['patent_id']
                        lat = row['inventor_add_lat']      
                        lng = row['inventor_add_lon']
                        inventor_id = row['inventor_id']
                        ungrouped.append((lat, lng, inventor_id))
                    
                else:
                    output_each_patent(ungrouped, patent, r1, r2)
                    
                    patent = row['patent_id']
                    lat = row['inventor_add_lat']
                    lng = row['inventor_add_lon']
                    inventor_id = row['inventor_id']
                    ungrouped = []
                    ungrouped.append((lat, lng, inventor_id))
                   
               
            
                
        
        
        
    