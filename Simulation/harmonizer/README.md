# Harmonizer
We need to run the harmonizer.py with the following arguments:
- [Required] **-f failures_input** -> Path to the failures_constraints.pl
- [Required] **-e energy_input** -> Path to the energy_constraints.pl
- [Optional] **-p failure/energy** -> Priority if needed.
- [Required] **-o output_file**  -> Path for the output files (prolog rules and YAML file).

**Examples:** <br/>
- python harmonizer.py -f failures_constraints.pl -e energy_constraints.pl -p failure -o outputfile
- python harmonizer.py -f failures_constraints.pl -e energy_constraints.pl -p energy -o outputfile
- python harmonizer.py -f failures_constraints.pl -e energy_constraints.pl -o outputfile

## Result
The harmonizer generates two files:
- A .pl file containing the merged constraints in Prolog format.
- A .yaml file containing the generated requirements.