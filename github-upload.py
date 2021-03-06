#!/usr/bin/env python


import json
import requests
import sys
import argparse
import os
import mimetypes
import pycurl
import cStringIO
from xml.dom import minidom

github_api_root = "https://api.github.com/"

def parse_args():
	parser = argparse.ArgumentParser(description='post a file to github as a download')
	parser.add_argument('--user', dest='user', help='github username', required=True)
	parser.add_argument('--pass', dest='password', help='github password', required=True)
	parser.add_argument('--repo', dest='repo', help='the name of the github repo', required=True)
	parser.add_argument('--file', dest='filepath', help='path of the local file to upload', required=True)
	parser.add_argument('--desc', dest='description', help='descriptive text about this file', required=True)
	parser.add_argument('--owner', dest='owner', help='owner of the github repository', required=True)
	args = parser.parse_args()
	# print args
	return args

def make_dl_post_url(owner, repo):
	url = "%srepos/%s/%s/downloads" % (str(github_api_root), str(owner), str(repo))
	# print url
	return url

def make_dl_delete_url(owner, repo, dlid):
	url = "%srepos/%s/%s/downloads/%s" % (str(github_api_root), str(owner), str(repo), str(dlid))
	# print url
	return url

def add_github_reference(args):
	dl_post_url = make_dl_post_url(args.owner, args.repo)

	fp = args.filepath
	filename = os.path.basename(fp)
	filesize = os.path.getsize(fp)

	mtype, mdetails = mimetypes.guess_type(fp)

	file_description = {
		'name': filename,
		'size': filesize,
		'description': args.description,
		'content_type': mtype
	}
	# print json.dumps(file_description, indent=2)

	github = requests.post(dl_post_url, auth=(args.user, args.password), data=json.dumps(file_description))
	resp = github.json
	# print json.dumps(resp, indent=2)
	return resp

def remove_github_reference(args, dlid):
	dl_delete_url = make_dl_delete_url(args.owner, args.repo, dlid)

	github = requests.delete(dl_delete_url, auth=(args.user, args.password))
	delete_ok = (204 == github.status_code)
	return delete_ok

def post_file_to_s3(file_path, gh):
	# s3 is very particular with field ordering

	# curl \
	# -F "key=downloads/octocat/Hello-World/new_file.jpg" \
	# -F "acl=public-read" \
	# -F "success_action_status=201" \
	# -F "Filename=new_file.jpg" \
	# -F "AWSAccessKeyId=1ABCDEF..." \
	# -F "Policy=ewogIC..." \
	# -F "Signature=mwnF..." \
	# -F "Content-Type=image/jpeg" \
	# -F "file=@new_file.jpg" \
	# https://github.s3.amazonaws.com/

	s3_ok = 201
	xml_buffer = cStringIO.StringIO()

	try:
		post_fields = [
			('key', str(gh['path'])),
			('acl', str(gh['acl'])),
			('success_action_status', str(s3_ok)),
			('Filename', str(gh['name'])),
			('AWSAccessKeyId', str(gh['accesskeyid'])),
			('Policy', str(gh['policy'])),
			('Signature', str(gh['signature'])),
			('Content-Type', str(gh['mime_type'])),
		  ('file', (pycurl.FORM_FILE, file_path))
		]
		# print post_fields

		s3 = pycurl.Curl()
		s3.setopt(pycurl.SSL_VERIFYPEER, 0)
		s3.setopt(pycurl.SSL_VERIFYHOST, 0)
		s3.setopt(pycurl.POST, 1)
		s3.setopt(pycurl.URL, str(gh['s3_url']))
		s3.setopt(pycurl.HTTPPOST, post_fields)
		# s3.setopt(pycurl.VERBOSE, 1)

		# accumulate string response
		s3.setopt(pycurl.WRITEFUNCTION, xml_buffer.write)

		s3.perform()

		file_upload_success = (s3_ok == s3.getinfo(pycurl.HTTP_CODE))
		xml_payload = minidom.parseString(xml_buffer.getvalue())

		if (file_upload_success):
			location_element = xml_payload.getElementsByTagName('Location')
			print location_element[0].firstChild.nodeValue
		else:
			print xml_payload.toprettyxml()


	except Exception, e:
		print e
		file_upload_success = False

	finally:
		s3.close()

	return file_upload_success


def main():
	mimetypes.init()
	args = parse_args()

	# step 1: tell github about the file
	gh = add_github_reference(args)

	# step 2: upload file to s3
	if ('errors' in gh):
		print json.dumps(gh, indent=2)
	else:
		file_upload_success = post_file_to_s3(args.filepath, gh)

		# cleanup if upload failed
		if (False == file_upload_success):
			removed_ok = remove_github_reference(args, gh['id'])
			if (removed_ok):
				print "removed github reference"
			else:
				print "failed to remove github reference"


if __name__ == '__main__':
	main()
