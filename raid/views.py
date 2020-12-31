from django.shortcuts import render
from django.http import HttpResponse
import requests 
from bs4 import BeautifulSoup
import json

guild = '431699'
	
def get_player_data(name, metric):
	URL = "https://www.warcraftlogs.com/v1/parses/character/" + name + "/Malganis/US?metric=" + metric + "&timeframe=historical&api_key=0993517430a99ecb7e93c9ab6441b1b6"
	r = requests.get(url = URL)
	info = json.loads(r.text)
	
	results_heroic = {}
	results_normal = {}
	for i in info:
		encounter_name = i["encounterName"]
		if encounter_name not in results_heroic:
			results_heroic[encounter_name] = []
		if encounter_name not in results_normal:
			results_normal[encounter_name] = []
			
		if i["difficulty"] == 3:
			results_normal[encounter_name].append(i["percentile"])
		if i["difficulty"] == 4:
			results_heroic[encounter_name].append(i["percentile"])
		
	final_heroic = {}
	final_normal = {}
	for key, val in results_heroic.items():
		if len(val) == 0:
			final_heroic[key] = {"max" : None, "med" : None} 
			continue
	
		final_heroic[key] = {"max" : 0, "med" : 0}
		final_heroic[key]["max"] = max(results_heroic[key])
		if len(results_heroic[key]) % 2 == 0:
			t0 = results_heroic[key][int(len(results_heroic[key]) / 2) - 1]
			t1 = results_heroic[key][int(len(results_heroic[key]) / 2)]
			final_heroic[key]["med"] = (t0 + t1) / 2
		else:
			final_heroic[key]["med"] = results_heroic[key][int(len(results_heroic[key]) / 2)]
			
		final_heroic[key]["med"] = (int)(final_heroic[key]["med"] + 0.5)
		final_heroic[key]["max"] = (int)(final_heroic[key]["max"] + 0.5)
		
	for key, val in results_normal.items():
		if len(val) == 0:
			final_normal[key] = {"max" : None, "med" : None} 
			continue
			
		final_normal[key] = {"max" : 0, "med" : 0}
		final_normal[key]["max"] = max(results_normal[key])
		if len(results_normal[key]) % 2 == 0:
			t0 = results_normal[key][int(len(results_normal[key]) / 2) - 1]
			t1 = results_normal[key][int(len(results_normal[key]) / 2)]
			final_normal[key]["med"] = (t0 + t1) / 2
		else:
			final_normal[key]["med"] = results_normal[key][int(len(results_normal[key]) / 2)]
			
		final_normal[key]["med"] = (int)(final_normal[key]["med"] + 0.5)
		final_normal[key]["max"] = (int)(final_normal[key]["max"] + 0.5)
			
	return {"heroic" : final_heroic, "normal" : final_normal}

args = {}

def load_data():
	URL = "https://www.warcraftlogs.com/guild/characters/" + guild + "/"
	
	r = requests.get(url = URL)
	soup = BeautifulSoup(r.text, 'html.parser')
	
	raid_team = []
	
	# Get a list of raid members
	for raid_member in soup.find_all('tr'):
		member = {}
		for data in raid_member.find_all('td'):
			data_class = data.get("class")
			if data_class and data_class[0] == "main-table-name":
				name = data.__dict__['contents'][2].string
				member["name"] = name
				
		if "name" in member:
			raid_team.append(member)
		
	bosses = ["Shriekwing", "Huntsman Altimor", "Hungering Destroyer", "Sun King's Salvation", "Artificer Xy'mox", "Lady Inerva Darkvein", "The Council of Blood", "Sludgefist", "Stone Legion Generals", "Sire Denathrius"]
	
	global args
	args = {"raiders" : [], "bosses":bosses}
	for member in raid_team:
		raider = {}
		raider["name"] = member["name"]
		summary = get_player_data(member["name"], "dps")
		healing = get_player_data(member["name"], "hps")

		raider["n_include"] = False
		raider["h_include"] = False
		
		raider["heroic"] = {}
		raider["normal"] = {}
		raider["heroic"]["dps"] = summary["heroic"]
		raider["normal"]["dps"] = summary["normal"]
		raider["heroic"]["hps"] = healing["heroic"]
		raider["normal"]["hps"] = healing["normal"]
		
		for boss in bosses:
			if boss in summary["heroic"] and (summary["heroic"][boss]["max"] or summary["heroic"][boss]["med"]):
				raider["h_include"] = True
			if boss in summary["normal"] and (summary["normal"][boss]["max"] or summary["normal"][boss]["med"]):
				raider["n_include"] = True
			if boss in healing["heroic"] and (healing["heroic"][boss]["max"] or healing["heroic"][boss]["med"]):
				raider["h_include"] = True
			if boss in healing["normal"] and (healing["normal"][boss]["max"] or healing["normal"][boss]["med"]):
				raider["n_include"] = True
		
		args["raiders"].append(raider)
		
	args["difficulty"] = "heroic"
	args["metric"] = "dps"
	args["statistic"] = "max"

def post(request):
	if len(args.keys()) == 0:
		load_data()
		
	if "difficulty" in request.POST:
		args["difficulty"] = request.POST["difficulty"]
	if "metric" in request.POST:
		args["metric"] = request.POST["metric"]
	if "statistic" in request.POST:
		args["statistic"] = request.POST["statistic"]
		
	return render(request, 'template.html', args)
	
def get(request):
	if len(args.keys()) == 0:
		load_data()
	return render(request, 'template.html', args)

def index(request):
	if request.method == 'POST':
		return post(request)
	if request.method == 'GET':
		return get(request)
	