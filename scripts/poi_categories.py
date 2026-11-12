"""Explicit OSM service categories. Religion comes only from mapped tags."""
ACCEPTED={'amenity':{'school','college','university','library','hospital','clinic','pharmacy','community_centre','bus_station','bank','place_of_worship'},'leisure':{'park','playground','fitness_centre','sports_centre'},'shop':{'supermarket','convenience','hairdresser_supply','cosmetics'},'railway':{'station','halt','tram_stop'}}
def classify(tags):
 if tags.get('access') in ['private','no']:return None
 category=next((tags[k] for k,vals in ACCEPTED.items() if tags.get(k) in vals),None)
 if category is None:return None
 category={'hairdresser_supply':'beauty_supply','fitness_centre':'gym','university':'college','halt':'station','tram_stop':'station'}.get(category,category)
 if tags.get('amenity')=='place_of_worship':category={'hindu':'hindu_temple','christian':'church','muslim':'mosque','jewish':'synagogue','buddhist':'buddhist_temple','sikh':'gurdwara'}.get(tags.get('religion',''),'other_worship')
 if tags.get('name','').lower() in {'sally beauty','sally beauty supply','saloncentric'}:category='beauty_supply'
 return category
