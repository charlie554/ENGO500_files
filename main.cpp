#include<iostream>
#include<sstream>
#include<fstream>
#include<stdio.h>
#include<stdlib.h>
#include<string>
#include<unistd.h>
//usleep()
void intSpeed();
void upload(int streamID, double value);

int dstream=156964;
int ustream=249072;

using namespace std;
int main()
{
	int timer = 12;
	while(1)
	{
		intSpeed();
		cout << endl << "waiting " << timer*5 << " seconds:" << endl;
		for(int i = 0 ; i <  timer ; i++)
		{
			usleep(5000000);
			cout << i*5+5 << "seconds have passed" << endl;
		}
		cout << endl;
	}
	return 0;

}

void intSpeed()
{
	system("python speedtest_cli.py > internet.txt");
	ifstream input;
	input.open("internet.txt");
	double down,up;
	string temp;
	while(!input.eof())
	{
		input >> temp;
		if(temp == "Download:")
			input >> down;
		if(temp == "Upload:")
			input >> up;
	}
	input.close();
	cout << "upload: " << up << "down: " << down << endl;
	cout << "uploading download speed" << endl;
	upload(dstream,down);
	cout << "uploading upload speed" << endl;
	upload(ustream,up);
	return;
}

void upload(int streamID, double value)
{
	stringstream convert1;
	stringstream convert2;
	convert1 << streamID;
	convert2 << value;

	string id = convert1.str();
	string val= convert2.str();
	string command;
	command =  "python upload.py " + id + " " + val;
	system(command.c_str());
	return;
}
