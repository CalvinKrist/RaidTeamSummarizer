from django import template

register = template.Library()

L = [8, 45]
none = " - "
	
@register.simple_tag
def get_raid_val(value, *args):
	boss = args[0]
	difficulty = args[1]
	metric = args[2]
	statistic = args[3]
	
	try:
		val = value[difficulty][metric][boss][statistic]
		return f'{val:02}'
	except:
		return none
		
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
		return none
		
@register.simple_tag
def get_raid_avg(value, *args):
	difficulty = args[0]
	metric = args[1]
	statistic = args[2]
	try:
		if statistic == "max":
			val = (int)(value[difficulty][metric]["max_avg"] + 0.5)
			return f'{val:02}'
		if statistic == "med":
			val = (int)(value[difficulty][metric]["med_avg"] + 0.5)
			return f'{val:02}'
		return ""
	except:
		return none
		
@register.simple_tag
def get_raid_avg_2(value, *args):
	boss = args[0]
	difficulty = args[1]
	metric = args[2]
	statistic = args[3]
	try:
		val = value[difficulty][metric][boss][statistic]
		return f'{val:02}'
	except:
		return none