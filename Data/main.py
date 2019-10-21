import os
import sys
from collections import Counter
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path)
import verbo.generate_verbo
import rico.generate_rico

def main():
	# generate pascal format dataset
	counts_V = verbo.generate_verbo.generate_pascal()
	# counts_V = Counter({'ImageButton': 71879, 'Button': 63956, 'CheckBox': 8787, 'ProgressBar': 6314, 'RadioButton': 5880, 'Spinner': 3198, 'ToggleButton': 2551, 'SeekBar': 2239, 'Switch': 1578, 'RatingBar': 1160, 'Chronometer': 25})
	counts_R = rico.generate_rico.generate_pascal()
	# counts_R = Counter({'ImageButton': 32606, 'Button': 26112, 'RadioButton': 5436, 'CheckBox': 4980, 'Spinner': 3495, 'Switch': 3186, 'ToggleButton': 2445, 'SeekBar': 1996, 'RatingBar': 1143, 'Chronometer': 32})
	counts = counts_V + counts_R
	# counts = Counter({'ImageButton': 104485, 'Button': 90068, 'CheckBox': 13767, 'RadioButton': 11316, 'Spinner': 6693, 'ProgressBar': 6314, 'ToggleButton': 4996, 'Switch': 4764, 'SeekBar': 4235, 'RatingBar': 2303, 'Chronometer': 57})

if __name__ == '__main__': 
	main()
