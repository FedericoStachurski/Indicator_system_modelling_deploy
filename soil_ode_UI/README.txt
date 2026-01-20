Soil ODE Interactive UI

This folder contains a small Streamlit application that provides an interactive interface for exploring a simple soil-health differential equation model. The interface uses sliders to adjust parameters and displays the results as plots.

###################### 1. Requirements ######################

You need Python 3.9+ and the following Python packages:
- streamlit
- numpy
- scipy
- matplotlib

If the project includes a requirements.txt file, you can install everything with:

pip install -r requirements.txt

###################### 2. Running the app locally ######################

If you are working on your own machine (laptop/desktop):

Open a terminal and go to the project folder.

Activate your Python environment (if you use one).

Run:

streamlit run soil_ode_UI/streamlit_soil_ode_UI.py


Streamlit will open a browser window automatically.
If it doesn’t, open the printed URL (usually http://localhost:8501).

###################### 3. Running the app on a remote server (SSH) ######################

If you are logged into a remote machine (e.g. a university server):

On the remote machine, run:

streamlit run soil_ode_UI/streamlit_soil_ode_UI.py


Streamlit will print something like:

Local URL: http://localhost:8501


Leave the app running.
Then, on your local computer, open a new terminal and create an SSH tunnel:

ssh -L 8501:localhost:8501 <username>@<remote-server-address>


After connecting, go to the following URL in your local web browser:

http://localhost:8501


You should now see the Streamlit interface, even though it is running remotely.

###################### 4. Stopping the app ######################

Press Ctrl + C in the terminal where Streamlit is running.

###################### 5. Editing the code ######################

The main file controlling the UI is:

soil_ode_UI/streamlit_soil_ode_UI.py


You can edit this file to adjust the model, parameters, or interface layout.