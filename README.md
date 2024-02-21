This short README describes how to run and test the file transfer application project.

	Step 1: create a new directory for the server and copy python script "server.py" into the directory

	Step 2: create a new directory for the client and copy python script "client.py" into the directory

	Step 3: copy test files from "./tests/" into directory created for client
 
	Step 4: open a command prompt and navigate to the directory created for server
 
	Step 5: run the server script, passing the port number and optional debug flag
	
 		> py server.py 2222	(debug DISABLE)
		> py server.py 2222 -d	(debug ENABLE)
		
	Step 6: open a second command prompt and navigate to the directory created for client
	
	Step 7: run the client script, passing the server IP, port number and optional debug flag
	
		> py client.py 192.168.2.22 2222	(debug DISABLE)
		> py client.py 192.168.2.22 2222 -d	(debug ENABLE)
		
		*** WARNING: IP and PORT input must match the server ***
		
	Step 10: test HELP command by entering the following in the client
	
		>> help
		
		* the server sends a string with the supported commands.
		
	Step 9: test PUT command using one of the test files, by entering the following in the client
	
		>> put test.txt
		>> put testPic.png
		>> put testDoc.docx
		>> put testVid.mp4
		>> put testSound.mp3
		
		* the file will be uploaded to the server directory from the client directory.
	
	Step 10: test CHANGE command on file PUT from Step 8, by entering one of the following in the client
	
		>> change test.txt testing.txt
		>> change testPic.png pic.png
		>> change testDoc.docx wordDoc.docx
		>> change testVid.mp4 video.mp4
		>> change testSound.mp3 sound.mp3
		
		* the file name will be changed in the server directory.
		
	Step 11: test GET command on file PUT and CHANGE from Steps 8-9, by entering one of the following in the client
	
		>> get testing.txt
		>> get pic.png
		>> get wordDoc.docx
		>> get video.mp4
		>> get sound.mp3
		
		* the file will be downloaded from server directory to client directory.
	
	Step 12: compare contents of all files, both in server and client directories, to make sure there's no data transfer errors
		
	Step 13: test commands with wrong number of arguments, filenames greater than 30 characters, and incorrect command names to further test client-server behavior

	Step 14: when finished, test BYE command by entering the following in the client
	
		>> bye
		
		* the client closes its socket, server closes its client-side socket and waits for a new connection
