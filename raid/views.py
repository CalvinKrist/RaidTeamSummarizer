from django.shortcuts import render
from django.http import HttpResponse
import requests 
from bs4 import BeautifulSoup
import json
import threading
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

guild = '431699'
NOT_LOADED = 0
LOADING = 1
LOADED = 2
state = NOT_LOADED
	
def get_player_data(name, metric):
	URL = "https://www.warcraftlogs.com/v1/parses/character/" + name + "/Malganis/US?metric=" + metric + "&timeframe=historical&api_key=0993517430a99ecb7e93c9ab6441b1b6"
	r = requests.get(url = URL)
	info = json.loads(r.text)
	
	if r.status_code != 200:
		print("ERROR")
		print(r.text)
		return -1
	
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
bosses = ["Shriekwing", "Huntsman Altimor", "Hungering Destroyer", "Sun King's Salvation", "Artificer Xy'mox", "Lady Inerva Darkvein", "The Council of Blood", "Sludgefist", "Stone Legion Generals", "Sire Denathrius"]

def parse_to_col(parse):
	if parse > 99:
		return "top"
	if parse >= 95:
		return "excellent"
	if parse >= 75:
		return "great"
	if parse >= 50:
		return "okay"
	if parse >= 25:
		return "bad"
	return "horrible"

def load_background_data(download):
	global state
	global args
	state = LOADING
	print("Loading background data.")
	
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
	
	for member in raid_team:
		raider = {}
		raider["name"] = member["name"]
		summary = get_player_data(member["name"], "dps")
		healing = get_player_data(member["name"], "hps")
		if not download or summary == -1 or healing == -1:
			with open('data.txt') as json_file:
				args = json.load(json_file)
			print("Background data loaded from cache.")
			state = LOADED
			
			return 

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
		
		
	for raider in args["raiders"]:
		diffs = [raider["heroic"], raider["normal"]]
		for diff in diffs:
			modes = [diff["dps"], diff["hps"]]
			for mode in modes:
				med_sum = 0
				max_sum = 0
				count = 0
				for boss, res in mode.items():
					if res["med"] != None:
						med_sum += res["med"]
						count += 1
						max_sum += res["max"]
				med_avg = 0
				max_avg = 0
				if count > 0:
					med_avg = med_sum / count
					max_avg = max_sum / count
				mode["max_avg"] = max_avg
				mode["med_avg"] = med_avg
				mode["max_col"] = parse_to_col(max_avg)
				mode["med_col"] = parse_to_col(med_avg)
				
	# Calculate Averages
	raider = {}
	raider["name"] = "Average"
	raider["n_include"] = True
	raider["h_include"] = True
	
	stats = ["max", "med"]
	metrics = ["dps", "hps"]
	modes = ["heroic", "normal"]
	boss_avg = {}
	for boss in bosses:
		boss_avg[boss] = {}
		for metric in metrics:
			boss_avg[boss][metric] = {}
			for mode in modes:
				boss_avg[boss][metric][mode] = {}
				for stat in stats:
					boss_avg[boss][metric][mode][stat] = {"sum" : 0, "count" : 0}
					
	for boss in bosses:
		for raid_member in args["raiders"]:
			modes = []
			if raid_member["n_include"]:
				modes.append("normal")
			if raid_member["h_include"]:
				modes.append("heroic")
			for metric in metrics:
				for mode in modes:
					for stat in stats:
						if boss in raid_member[mode][metric]:
							if raid_member[mode][metric][boss][stat] != None:
								boss_avg[boss][metric][mode][stat]["sum"] += raid_member[mode][metric][boss][stat]
								boss_avg[boss][metric][mode][stat]["count"] += 1
						
	modes = ["heroic", "normal"]
	for mode in modes:
		raider[mode] = {}
		for metric in metrics:
			raider[mode][metric] = {}
			for boss in bosses:
				raider[mode][metric][boss] = {}
				for stat in stats:
					if boss_avg[boss][metric][mode][stat]["count"] == 0:
						raider[mode][metric][boss][stat] = None
					else:
						raider[mode][metric][boss][stat] = (int)(boss_avg[boss][metric][mode][stat]["sum"] / boss_avg[boss][metric][mode][stat]["count"] + 0.5)
	
	args["average"] = raider
		
	print("Background data loaded.")
	state = LOADED
	
	with open('data.txt', 'w') as outfile:
		json.dump(args, outfile)

def load_data(download=False):	
	global args
	global state
	state = NOT_LOADED
	args = {"raiders" : [], "bosses":bosses}
	args["difficulty"] = "heroic"
	args["metric"] = "dps"
	args["statistic"] = "max"
	
	t = threading.Thread(target=load_background_data, args=(download,))
	t.start()
	
def post(request):
	global state
	global args
	if state == NOT_LOADED:
		load_data()
		
	if "difficulty" in request.POST:
		args["difficulty"] = request.POST["difficulty"]
	if "metric" in request.POST:
		args["metric"] = request.POST["metric"]
	if "statistic" in request.POST:
		args["statistic"] = request.POST["statistic"]
	if "refresh" in str(request.body):
		if state != NOT_LOADED:
			state = NOT_LOADED
			load_data(download=True)
		
	return render(request, 'template.html', args)
	
def get(request):
	if state == NOT_LOADED:
		load_data()
		
	global args
	return render(request, 'template.html', args)

@csrf_exempt
def index(request):
	if request.method == 'POST':
		return post(request)
	if request.method == 'GET':
		return get(request)
	
@csrf_exempt
def done(request):
	global state
	print(state)
	data = {
        'done': state==LOADED
    }
	return JsonResponse(data)