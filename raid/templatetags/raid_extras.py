from django import template

register = template.Library()
	
@register.simple_tag
def get_raid_val(value, *args):
	boss = args[0]
	difficulty = args[1]
	metric = args[2]
	statistic = args[3]
	return value[difficulty][metric][boss][statistic]