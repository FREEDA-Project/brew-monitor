# Failure Enhancer
## Step 1
First we need to run eclypseParser.py with the following arguments:
- [Required] **-i path/input** -> Path to simulation.log that we want to process.
- [Required] **-o path/output** -> Path for the prolog facts that will be generated.

**Example:** <br/>
python eclypseParser.py -i simulation.log -o failures_input

The script will generate the input needed to run the failureEnhancer.pl 

## Step 2
We run the Failure Enhancer using the "--" flag, with the following arguments:
- Path to the input_file.pl (file that contains the prolog facts)
- Path for the output_file.pl (file that constains the generated constraints)

**Example:** <br/>
swipl -q -s failureEnhancer.pl -- failures_input.pl failures_constraints.pl

## Result
The Failure Enhancer will generate the failures_constraints to be used by the Harmonizer.