import agentforge

# Load and run a cog
cog = agentforge.Cog('example_cog')
response = cog.run({'user_input': 'What is the capital of France?'})
print(response)