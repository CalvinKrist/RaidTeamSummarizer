from django import template

register = template.Library()
	
@register.simple_tag
def get_raid_val(value, *args):
	boss = args[0]
	difficulty = args[1]
	metric = args[2]
	statistic = args[3]
	try:
		return value[difficulty][metric][boss][statistic]
	except:
		return "None"
		
@register.simple_tag
def get_raid_color(value, *args):
	difficulty = args[0]
	metric = args[1]
	statistic = args[2]
	try:
		if statistic == "max":
			return value[difficulty][metric]["max_col"]
		if statistic == "med":
			return value[difficulty][metric]["med_col"]
		return ""
	except:
		return "None"
		
@register.simple_tag
def get_raid_avg(value, *args):
	difficulty = args[0]
	metric = args[1]
	statistic = args[2]
	try:
		if statistic == "max":
			return (int)(value[difficulty][metric]["max_avg"] + 0.5)
		if statistic == "med":
			return (int)(value[difficulty][metric]["med_avg"] + 0.5)
		return ""
	except:
		return "None"
		
@register.simple_tag
def get_raid_avg_2(value, *args):
	boss = args[0]
	difficulty = args[1]
	metric = args[2]
	statistic = args[3]
	try:
		return value[difficulty][metric][boss][statistic]
	except:
		return "None"