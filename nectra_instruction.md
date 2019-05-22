# Connection
- $ssh -i ~/.ssh/zheping-tweets-clustering.pem ubuntu@203.101.226.165

# Scp
## upload to vm
- $scp -i ~/.ssh/zheping-tweets-clustering.pem (local address) ubuntu@203.101.226.165:~/ResearchProject
## download from vm
- $scp -i ~/.ssh/Nectar_Key ubuntu@NNN.NNN.NNN.NNN:<instance-file-path> <local-file-path>

# editor
- $nano (file name)
- ctrl + O, then Enter to save
- ctrl + X to exit

# Never off session
- $tmux
- exit the session: ctrl + B, then press d
- resume the session: $tmux attach