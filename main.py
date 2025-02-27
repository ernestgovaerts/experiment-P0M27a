from psychopy import visual, core, event, gui, data
import random
import os
import pandas as pd

# Experiment metadata
expName = 'Experiment-P0M27a'
expInfo = {'Participant': '', 'Sessie': '', 'Date': data.getDateStr(format='%d-%m-%Y_%H:%M')}
dlg = gui.DlgFromDict(dictionary=expInfo, sortKeys=False, title=expName)
if not dlg.OK:
    core.quit()

#CONDITIE 1: happy_go_first
#CONDITIE 2: sad_go_first

def get_count(condition):
    return 0

data_dir = "data"
os.makedirs(data_dir, exist_ok=True)
file_path = os.path.join(data_dir, f"participant_{expInfo['Participant']}.csv")

def log_trial(participant, condition, block, stimulus, response, rt, correct):
    global df
    new_data = pd.DataFrame([{
        "Participant": participant,
        "Condition": condition,
        "Block": block,
        "Stimulus": stimulus,
        "Response": response,
        "RT": rt,
        "Correct": correct
    }])
    df = pd.concat([df, new_data], ignore_index=True)

columns = ["Participant", "Condition", "Block", "Stimulus", "Response", "RT", "Correct"]
df = pd.DataFrame(columns=columns)

# Wijs participant toe aan "happy_go_first" (1) dan wel "sad_go_first" (0) conditie
def assign_condition():
    happy_go_first_count = get_count("happy_go_first")
    sad_go_first_count = get_count("sad_go_first")

    if happy_go_first_count < sad_go_first_count:
        return 1  # Meer deelnemers die eerst sad gezichten kregen, dus wijs happy_go_first toe
    elif sad_go_first_count < happy_go_first_count:
        return 0  # Meer deelnemers die eerst happy gezichten kregen, dus wijs sad_go_first toe
    return random.choice([0, 1])  # Random toewijzing als counts gelijk zijn

expInfo["assigned_condition"] = assign_condition()

stimuli_dir = "stimuli"


def get_random_image(category):
    """Fetches a random image from the specified category directory."""
    category_path = os.path.join(stimuli_dir, category)

    # Check if the directory exists
    if not os.path.exists(category_path):
        print(f"Directory does not exist: {category_path}")
        return None

    # List images and filter by extension
    images = [img for img in os.listdir(category_path) if img.lower().endswith((".jpg", ".png"))]

    # Debugging: print available images
    print(f"Available images in {category_path}: {images}")

    if not images:
        print(f"No images found in {category_path}")
        return None

    return os.path.join(category_path, random.choice(images))


# Open window
win = visual.Window(fullscr=True, color="gray", units="pix")

# Instructies
instruction_text = (
    "Welkom bij dit experiment!\n\n"
    "In deze Go/No-Go-taak moet je reageren op bepaalde gezichten (Go-stimulus) "
    "en niet reageren op andere gezichten (No-Go-stimulus). \n"
    "De uitdrukking van de gezichten kan blij of verdrietig zijn.\n\n"
    "De taak is verdeeld in twee delen. Na het eerste deel verandert welke gezichten "
    "de Go- en No-Go-stimuli zijn.\n\n"
    "Voor elk deel krijg je een korte instructie over welke gezichten de Go- en No-Go-stimuli zijn.\n\n"
    "Je reageert door op de spatiebalk te drukken.\n\n"
    "Druk op [F] om door te gaan."
)
visual.TextStim(win, text=instruction_text, color="white", wrapWidth=1000, height=25).draw()
win.flip()
event.waitKeys(keyList=["f"])


# Go/No-Go blocks
for block in range(2):
    is_first_block = block == 0
    go_stimuli = "BLIJE" if (expInfo["assigned_condition"] == 1) == is_first_block else "VERDRIETIGE"
    no_go_stimuli = "VERDRIETIGE" if go_stimuli == "BLIJE" else "BLIJE"



    go_example_path = get_random_image(go_stimuli)
    no_go_example_path = get_random_image(no_go_stimuli)

    print(go_example_path, no_go_example_path)

    # Block Instructions
    instruction_text = (f"Deel {block + 1} van 2\n\nIn dit deel zijn {go_stimuli} gezichten de Go-stimuli.\n" +
                        f"De {no_go_stimuli} gezichten zijn dus de No-Go-stimuli.\n\nDruk op [F] om door te gaan.")
    visual.TextStim(win, text=instruction_text, color="white", wrapWidth=1000, height=25).draw()

    # Voorbeelden van Go- en No-Go-stimuli
    if go_example_path and no_go_example_path:
        go_example = visual.ImageStim(win, image=go_example_path, pos=(-200, -300), size=(220, 300))
        subtext = "Go-stimulus" if go_stimuli == "BLIJE" else "No-Go-stimulus"
        visual.TextStim(win, text=subtext, pos=(-190, -140), color="white", height=20).draw()
        no_go_example = visual.ImageStim(win, image=no_go_example_path, pos=(200, -300), size=(220,300))
        subtext = "Go-stimulus" if no_go_stimuli == "BLIJE" else "No-Go-stimulus"
        visual.TextStim(win, text=subtext, pos=(190, -140), color="white", height=20).draw()
        go_example.draw()
        no_go_example.draw()

    win.flip()
    event.waitKeys(keyList=["f"])

    # Main trial loop
    for trial in range(5):
        # Randomly select a Go or No-Go stimulus
        is_go_trial = random.choice([True, False])
        category = go_stimuli if is_go_trial else no_go_stimuli
        stimulus_path = get_random_image(category)

        # Present stimulus
        stimulus = visual.ImageStim(win, image=stimulus_path, size=(500, 500))
        stimulus.draw()
        win.flip()

        # Wacht op reactie
        response = event.waitKeys(keyList=["space", "escape"])
        if "escape" in response:
            core.quit()

        # Log trial data
        log_trial(expInfo["Participant"], expInfo["assigned_condition"], block + 1, stimulus_path, response[0], 0, is_go_trial)

    # Stop experiment als "escape" wordt ingedrukt
    if "escape" in event.getKeys():
        core.quit()

# Example: Log some trials dynamically during the experiment

# Save at the end
df.to_csv(file_path, index=False)
print(f"Data saved: {file_path}")

# Stop experiment
win.close()
core.quit()
