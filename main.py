from psychopy import visual, core, event, gui, data
import random
import os
import pandas as pd

# Experiment metadata en dialoogvenster
expName = 'Experiment-P0M27a'
expInfo = {'Participant': ''}
dlg = gui.DlgFromDict(dictionary=expInfo, sortKeys=False, title=expName)
if not dlg.OK:
    core.quit()

# Toewijzing aan een conditie (1:Go-eerst of 2:No-Go-eerst)
condition = 1 if int(expInfo["Participant"]) % 2 == 0 else 2
expInfo["assigned_condition"] = condition

# Locaties data initialiseren
data_dir = "data"
os.makedirs(data_dir, exist_ok=True)
file_name_exp = f"p{int(expInfo['Participant']):02d}"
file_path_exp = os.path.join(data_dir, f"{file_name_exp}.csv")
file_name_mc = f"mc_p{int(expInfo['Participant']):02d}.csv"
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
    visual.TextStim(win, text=text, color="white", wrapWidth=1000, height=25).draw()
    win.flip()
    event.waitKeys(keyList=["f"])

def extract_emotion(image_name):
    """Bepaalt de emotie van een stimulus op basis van de bestandsnaam."""
    return "Blij" if image_name[4].upper() == "H" else "Verdrietig"

# Lijst om trial-data in op te slaan
data_exp_records = []
data_mc_records = []

def save_data():
    """Slaat alle verzamelde data op in een CSV-bestand."""
    pd.DataFrame(data_exp_records).to_csv(file_path_exp, index=False)
    pd.DataFrame(data_mc_records).to_csv(file_path_mc, index=False)
    print(f"Experimentele data opgeslagen in {file_path_exp}")
    print(f"Manipulatiecheck-data opgeslagen in {file_path_mc}")

# Manipulatiecheck vragen
def ask_question(question_text, labels, ID):
    ticks = list(range(1, len(labels) + 1))  # Maak ticks op basis van het aantal labels
    question = visual.TextStim(win, text=question_text, color="white", height=35, wrapWidth=800, pos=(0, 200),
                               font="Arial")
    slider = visual.Slider(win, ticks=ticks, labels=labels,
                           granularity=1, style=["rating"], size=(600, 40), pos=(0, 0), color="white",
                           labelColor="white", font="Arial")
    instruction = visual.TextStim(win, text="Druk op [F] om verder te gaan", color="white", height=25, pos=(0, -200), font="Arial")

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

    data_mc_records.append({
        "Participant": expInfo["Participant"],
        "ID": ID,
        "Response": response
    })

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
        data_exp_records.append({
            "Participant": expInfo["Participant"],
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

# Experiment flow met instructies en trials
show_instructions(
    "Welkom!\n\n"
    "In dit experiment zal je blije en verdrietige gezichten te zien krijgen.\n"
    "Op het volgende scherm zie je in welke conditie je zit. "
    "Daar wordt aangegeven welke gezichtsuitdrukking de go-stimulus is (waarop je moet reageren) en "
    "welke de no-go-stimulus is (waarop je niet mag reageren). "
    "Het is belangrijk dat je dit goed onthoudt.\n\n"
    "Het experiment bestaat uit zes blokken, verdeeld over twee delen van drie blokken. \n"
    "Na het eerste deel beantwoord je een vraag over de taak, gevolgd door een korte pauze van 30 seconden. "
    "Daarna wisselen de gezichtsuitdrukkingen (blij/verdrietig) waarvoor je moet reageren (go) en niet mag reageren (no-go) van rol.\n\n"
    "Voor elk deel krijg je eerst een korte oefenronde waarin je kunt wennen aan de taak. "
    "Als je een fout maakt, krijg je kort feedback. Bij een juist antwoord krijg je geen feedback.\n\n"
    "Druk op [F] om verder te gaan."
)

show_instructions(
    f"In dit deel zijn {'BLIJE' if condition == 1 else 'VERDRIETIGE'} gezichten de Go-stimuli. "
    f"Dit betekent dat je op de spatiebalk moet drukken wanneer je deze gezichten ziet.\n\n"
    f"{'VERDRIETIGE' if condition == 1 else 'BLIJE'} gezichten zijn de No-Go-stimuli. "
    f"Je mag hier niet op reageren.\n\n"
    "Druk op [F] om verder te gaan."
)
show_instructions("Oefenronde 1. \n\n Druk op [F] om te starten.")
run_trials(first_practice, "Practice 1")

for i in range(3):
    show_instructions(f"Blok {i + 1}. \n\n Druk op [F] om te starten")
    run_trials(blocks[i], i + 1)

# Eerste manipulatiecheck
if condition == 1:
    ask_question("Hoe vaak heb je op de spatiebalk gedrukt bij een blije gezichtsuitdrukking?", ["Bijna nooit of nooit", "Zelden", "Soms", "Vaak", "Bijna altijd of altijd"], ID="mc1")
else:
    ask_question("Hoe vaak heb je op de spatiebalk gedrukt bij een verdrietige gezichtsuitdrukking?", ["Bijna nooit of nooit", "Zelden", "Soms", "Vaak", "Bijna altijd of altijd"], ID="mc2")

# Pauze van 30 seconden tussen de twee delen van het experiment
visual.TextStim(win, text="Einde van het eerste deel. \n U krijgt nu een pauze van 30 seconden, waarna de instructies voor het tweede deel zullen volgen.", color="white", wrapWidth=1000, height=25).draw()
win.flip()
core.wait(30)

# Omkeren van de go/no-go toewijzing voor het tweede deel
show_instructions(
    f"Vanaf nu zijn {'VERDRIETIGE' if condition == 1 else 'BLIJE'} gezichten de Go-stimuli \n en {'BLIJE' if condition == 1 else 'VERDRIETIGE'} gezichten de No-Go-stimuli. \n\n Druk op [F] om verder te gaan."
)
show_instructions("Oefenronde 2. \n\n Druk op [F] om te starten.")
run_trials(second_practice, "Practice 2")

for i in range(3, 6):
    show_instructions(f"Blok {i + 1}. \n\n Druk op [F] om te starten.")
    run_trials(blocks[i], i + 1)

show_instructions(
    "Je hebt alle blokken doorlopen. \n\n"
    "Voor we het experiment afsluiten, moet je nog kort twee vragen beantwoorden.\n"
    "Deze vragen gaan over de taak die je net hebt uitgevoerd. \n\n"
    "Druk op [F] om verder te gaan."
)
# Tweede manipulatiecheck
if condition == 2:
    ask_question("Hoe vaak heb je op de spatiebalk gedrukt bij een blije gezichtsuitdrukking?", ["Bijna nooit of nooit", "Zelden", "Soms", "Vaak", "Bijna altijd of altijd"], ID="mc1")
else:
    ask_question("Hoe vaak heb je op de spatiebalk gedrukt bij een verdrietige gezichtsuitdrukking?", ["Bijna nooit of nooit", "Zelden", "Soms", "Vaak", "Bijna altijd of altijd"], ID="mc2")

# Derde en vierde manipulatiecheck
ask_question("De tijd die ik had om te reageren op de stimulus was:", ["Altijd hetzelfde", "Meestal hetzelfde, met enkele uitzonderingen", "Sterk variërend tussen trials"], ID="mc3")
ask_question("Het verschil tussen de gezichtsuitdrukkingen was duidelijk.", ["Niet akkoord", "Neutraal", "Akkoord"], ID="mc4")


# Data opslaan en experiment afsluiten
save_data()
show_instructions(
    "Bedankt voor je deelname! \n\n"
    "Je antwoorden en reacties zullen anoniem worden verwerkt en geanalyseerd.\n\n"
    "Je mag nu de testleider verwittigen dat je klaar bent.\n\n"
)
win.close()
core.quit()
