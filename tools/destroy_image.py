import sys
import googleapiclient.discovery
import config as conf

compute = googleapiclient.discovery.build('compute', 'v1')

if len(sys.argv) > 1:
    SNAPSHOT_NAME = sys.argv[1]
else:
    raise Exception("No snapshot name specified")

print("Destroying image named: {name}...".format(
    name=SNAPSHOT_NAME))

# Destroy image

print('Deleting image...')
delete = compute.images().delete(project=conf.GCP_DEFAULT_PROJECT,
                                 image=SNAPSHOT_NAME).execute()
print('Image deleted')
