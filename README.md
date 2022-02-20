# Tolino Upload
A simple script for uplaoding files to tolino cloud.
For using this script you need to have a valid hardware_id, access_token and refresh_token of your client. You can get this information by login into the webreader using a browser and catch the information from the network requests.

Put the information into a config-file based on the example `config-example.yaml`

After that you might be able to upload files by 

`./tolinoUpload.py --config <your_config_file> --client <name_of_the_client_in_your_config> --debug --filename <the_file_to_upload>`
