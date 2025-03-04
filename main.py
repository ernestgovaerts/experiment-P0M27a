from psychopy import visual, core, event, gui, data
import random
import os
import pandas as pd

# Experiment metadata en dialoogvenster
expName = 'Experiment-P0M27a'
expInfo = {'Participant': '', 'Sessie': ''}
dlg = gui.DlgFromDict(dictionary=expInfo, sortKeys=False, title=expName)
if not dlg.OK:
    core.quit()

# Toewijzing aan een conditie (1:Go-first of 2:No-Go-first)
condition = 1 if int(expInfo["Participant"]) % 2 == 0 else 2
expInfo["assigned_condition"] = condition

# Locaties data initialiseren
data_dir = "data"
os.makedirs(data_dir, exist_ok=True)
file_name_exp = f"p{int(expInfo['Participant']):02d}s{int(expInfo['Sessie'])}"
file_path_exp = os.path.join(data_dir, f"{file_name_exp}.csv")
file_name_mc = f"mc_p{int(expInfo['Participant']):02d}s{int(expInfo['Sessie'])}.csv"
file_path_mc = os.path.join(data_dir, file_name_mc)

# Functies voor het laden en randomiseren van trial-bestanden
stimuli_dir = "stimuli/trials"

def load_trials(filename):
    """Laadt een Excel-bestand met trials en geeft een DataFrame terug."""
    path = os.path.join(stimuli_dir, filename)
    return pd.read_excel(path)

def shuffle_trials(trial_data):
    """Shuffle de rijen in een trialbestand en reset de index."""
    return trial_data.sample(frac=1).reset_index(drop=True)

# Laden en shufflen van de trials per conditie
first_practice = shuffle_trials(load_trials(f"First_Practtrials_Condition{condition}.xlsx"))
second_practice = shuffle_trials(load_trials(f"Second_Practtrials_Condition{condition}.xlsx"))
blocks = [shuffle_trials(load_trials(f"trialsBlock{i}_Condition{condition}.xlsx")) for i in range(1, 7)]

# Open een PsychoPy-venster voor het experiment
win = visual.Window(fullscr=True, color="#242424", units="pix", checkTiming=False)

def show_instructions(text):
    """Toont een instructietekst en wacht tot de deelnemer op [F] drukt om verder te gaan."""
    visual.TextStim(win, text=text, color="white", wrapWidth=1000, height=35).draw()
    win.flip()
    event.waitKeys(keyList=["f"])

def extract_emotion(image_name):
    """Bepaalt de emotie van een stimulus op basis van de bestandsnaam."""
    return "Blij" if image_name[4].upper() == "H" else "Verdrietig"

# Lijst om trial-data in op te slaan
data_records = []

def save_data():
    """Slaat alle verzamelde data op in een CSV-bestand."""
    pd.DataFrame(data_records).to_csv(file_path_exp, index=False)
    print(f"Data opgeslagen in {file_path_exp}")

def run_trials(trial_data, block_number):
    """Voert de trials uit voor een blok en registreert de response en reactietijden.
    De stimulus wordt 250ms getoond, gevolgd door een ISI van 200-1000ms.
    Gedurende de volledige trial wordt op respons geluisterd, maar feedback komt pas na de trial."""
    for _, trial in trial_data.iterrows():
        # Zorg dat vorige key events niet interfereren
        event.clearEvents()

        img_path = trial["image"]
        stimulus = visual.ImageStim(win, image=img_path, size=(500, 500))
        is_go = trial["stimulus"] == "go"
        isi_duration = random.uniform(0.2, 1.0)  # ISI tussen 200 en 1000 ms
        emotion = extract_emotion(os.path.basename(img_path))
        response, rt = None, None

        total_duration = 0.25 + isi_duration  # Totale trialduur in seconden
        trial_timer = core.Clock()  # Start de klok vanaf het begin van de stimulus

        # Voer de trial-loop uit voor de totale trialduur
        while trial_timer.getTime() < total_duration:
            current_time = trial_timer.getTime()

            # Teken de stimulus tijdens de eerste 250ms
            if current_time < 0.25:
                stimulus.draw()
            else:
                # ISI: laat een leeg scherm zien
                pass

            win.flip()

            # Controleer op keypresses gedurende de gehele trial
            keys = event.getKeys(keyList=["space", "escape"], timeStamped=trial_timer)
            if keys and response is None:
                for key, key_time in keys:
                    if key == "escape":
                        save_data()
                        core.quit()
                    elif key == "space":
                        response = "space"
                        rt = key_time  # RT gemeten vanaf het begin van de stimulus

            core.wait(0.005)  # Kleine pauze om CPU-gebruik te beperken

        # Na de trial: bepaal de feedback (wordt pas na stimulus en ISI getoond)
        if response is None and is_go:
            feedback_text = "Incorrect. \nJe moest op [SPATIE] drukken."
            correct = False
        elif response == "space" and not is_go:
            feedback_text = "Incorrect. \nJe mocht niet reageren."
            correct = False
        else:
            feedback_text = None
            correct = True

        if feedback_text:
            visual.TextStim(win, text=feedback_text, color="#e65c5c", wrapWidth=1000, height=35).draw()
            win.flip()
            core.wait(1.5)

        # Sla trialdata op
        data_records.append({
            "Participant": expInfo["Participant"],
            "Session": expInfo["Sessie"],
            "Block": block_number,
            "Image": img_path,
            "ISI": isi_duration,
            "StimulusType": "Go" if is_go else "No-Go",
            "Emotion": emotion,
            "Response": response,
            "Correct": correct,
            "ReactionTime": rt
        })

        # Sla data op indien vroegtijdig afgebroken
        if response == "escape":
            save_data()
            core.quit()


question = visual.TextStim(win, text="Hoe moeilijk vond je deze taak?", color="white", height=35, wrapWidth=800, pos=(0, 200), font="Arial")
slider = visual.Slider(win, ticks=[1, 2, 3, 4, 5], labels=["Heel makkelijk", "Makkelijk", "Gemiddeld", "Moeilijk", "Heel moeilijk"],
                        granularity=1, style=["rating"], size=(600, 40), pos=(0, 0), color="white", labelColor="white", font="Arial")
instruction = visual.TextStim(win, text="Druk op [F] om verder te gaan", color="white", height=25, pos=(0, -200))

# Vraag en slider tonen
response = None
while response is None:
    question.draw()
    slider.draw()
    instruction.draw()
    win.flip()

    keys = event.getKeys(keyList=["f", "escape"])
    if "f" in keys and slider.getRating() is not None:
        response = slider.getRating()
    elif "escape" in keys:
        core.quit()

# Data opslaan
data_record = pd.DataFrame([{
    "Participant": expInfo["Participant"],
    "Session": expInfo["Sessie"],
    "DifficultyRating": response
}])

data_record.to_csv(file_path_mc, index=False)
print(f"Data opgeslagen in {file_path_mc}")

# Experiment flow met instructies en trials
show_instructions("Welkom bij het experiment. \n\n Druk op [F] om verder te gaan.")
show_instructions(
    f"In dit deel zijn {'BLIJE' if condition == 1 else 'VERDRIETIGE'} gezichten de Go-stimuli \n en {'VERDRIETIGE' if condition == 1 else 'BLIJE'} gezichten de No-Go-stimuli. \n\n Druk op [F] om verder te gaan."
)
show_instructions("Oefenronde 1 begint nu. \n\n Druk op [F] om verder te gaan.")
run_trials(first_practice, "Practice 1")

for i in range(3):
    show_instructions(f"Blok {i + 1} begint nu. \n\n Druk op [F] om verder te gaan.")
    run_trials(blocks[i], i + 1)

# Pauze van 30 seconden tussen de twee delen van het experiment
show_instructions(
    "Einde van het eerste deel. \n U krijgt nu een pauze van 30 seconden, waarna de instructies voor het tweede deel zullen volgen.")
core.wait(30)

# Omkeren van de go/no-go toewijzing voor het tweede deel
show_instructions(
    f"Vanaf nu zijn {'VERDRIETIGE' if condition == 1 else 'BLIJE'} gezichten de Go-stimuli \n en {'BLIJE' if condition == 1 else 'VERDRIETIGE'} gezichten de No-Go-stimuli. \n\n Druk op [F] om verder te gaan."
)
show_instructions("Oefenronde 2 begint nu. \n\n Druk op [F] om verder te gaan.")
run_trials(second_practice, "Practice 2")

for i in range(3, 6):
    show_instructions(f"Blok {i + 1} begint nu. \n\n Druk op [F] om verder te gaan.")
    run_trials(blocks[i], i + 1)

# Data opslaan en experiment afsluiten
save_data()
show_instructions("Experiment voltooid. \n\n Bedankt voor je deelname!")
win.close()
core.quit()
