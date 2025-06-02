import kagglehub

# Download latest version
path = kagglehub.dataset_download("leeast/mmod-human-face-detector-dat")

print("Path to dataset files:", path)