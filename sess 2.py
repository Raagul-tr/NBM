from psychopy import visual, core, event, data, gui, monitors
import os, csv, random
import pandas as pd

os.chdir(r"https://github.com/Raagul-tr/NBM")

# ---------------------------------------------------------
# Utility: Get slider response with the specified question
# ---------------------------------------------------------
def get_slider_response(win, question, slider, rt_clock):
   
    slider.reset()
    rt_clock.reset()
    question_text = visual.TextStim(
        win=win,
        text=question,
        pos=(0, 100),  # pixels
        color='white',
        height=48,
        wrapWidth=1500
    )
    rating = None
    while rating is None:
        if event.getKeys(keyList=['escape']):
            win.close()
            core.quit()
        question_text.draw()
        slider.draw()
        win.flip()
        rating_val = slider.getRating()
        if rating_val is not None:
            rating = int(round(rating_val))
    rt = rt_clock.getTime()
    return rating, rt


# RECOGNITION PHASE

def run_recognition_phase(win, slider, rt_clock, excel_file):
    """
    1. Shows instructions.
    2. Loads words from the Excel file (columns: words, Type, old_new, y_n)
       and adds an 'excel_order' field.
    3. Randomizes the presentation order.
    4. key response ('y' or 'n').
       If the participant presses 'y', two 8-point ratings (belief and memory) 
    5. A new field 'presentation_order' is added to the trial data.
     """
   
    instructions = visual.TextStim(
        win=win,
        text=(
            "Welcome to the Recognition Test.\n\n"
            "Press 'y' if the word was already presented to you,\n'n' if the word is new.\n\n"
            "If you press 'y', you will be asked two additional questions about your\nrecollection and belief.\n\n"
            "Press SPACE to proceed."
        ),
        font='Arial',
        height=36,
        color='white',
        wrapWidth=1500
    )
    instructions.draw()
    win.flip()
    key = event.waitKeys(keyList=['space', 'escape'])
    if key and key[0]=='escape':
        win.close()
        core.quit()

    # Display "Are you ready?" screen (left-aligned)
    ready_text = visual.TextStim(
        win=win,
        text="Recollection: refers to the mental reexperiencing of an event (word)\nIn recollection rating, you will rate how detailed the word is reimaginable in your mind\n\n"
        "Belief: refers to the extent to which you believe the word was presented to you.\nIn belief rating, you want to rate how much true do you think the word is presented to you\n\n"
        "Press SPACE to start the test",
        height=36,
        color='white',
        wrapWidth=1500,
        pos=(0, 0)  
    )
    ready_text.draw()
    win.flip()
    key = event.waitKeys(keyList=['space', 'escape'])
    if key and key[0]=='escape':
        win.close()
        core.quit()

    if not os.path.exists(excel_file):
        print(f"Error: File {excel_file} not found!")
        win.close()
        core.quit()

    df = pd.read_excel(excel_file)
    df['excel_order'] = df.index
    df = df.sample(frac=1).reset_index(drop=True)

    trial_list = []
    for i, row in df.iterrows():
        trial_data = {}
        trial_data['excel_order'] = row['excel_order']
        trial_data['presentation_order'] = i + 1  # record order
        trial_data['word'] = str(row['words'])
        trial_data['Type'] = str(row['Type'])
        trial_data['old_new'] = str(row['old_new'])
        trial_data['y_n'] = str(row['y_n']).strip().lower()

        word_stim = visual.TextStim(
            win=win,
            text=trial_data['word'],
            font='Arial',
            height=48,
            color='white',
            wrapWidth=1500
        )
        word_stim.draw()
        win.flip()

        rt_clock.reset()
        keys = event.waitKeys(keyList=['y', 'n', 'escape'], timeStamped=rt_clock)
        if not keys:
            continue  
        response_key, response_rt = keys[0]
        if response_key == 'escape':
            win.close()
            core.quit()
        trial_data['recognition_response'] = response_key
        trial_data['recognition_rt'] = response_rt

        if response_key == 'y':
            memory_question = (
                "Do you actually remember that this word has appeared before?\n"
                "(1 = no memory of the word at all, 8 = clear and complete memory)"
            )
            memory_rating, memory_rt = get_slider_response(win, memory_question, slider, rt_clock)
            belief_question = (
                "Do you believe that this word has appeared before\n"
                "(regardless of whether you remember or not)?\n"
                "(1 = definitely did not happen, 8 = definitely did happen)"
            )
            belief_rating, belief_rt = get_slider_response(win, belief_question, slider, rt_clock)
            
            trial_data['belief_rating'] = belief_rating
            trial_data['belief_rt'] = belief_rt
            trial_data['memory_rating'] = memory_rating
            trial_data['memory_rt'] = memory_rt
        else:
            trial_data['belief_rating'] = None
            trial_data['belief_rt'] = None
            trial_data['memory_rating'] = None
            trial_data['memory_rt'] = None

        # challenge rating 
        trial_data['challenge_belief_rating'] = None
        trial_data['challenge_belief_rt'] = None
        trial_data['challenge_memory_rating'] = None
        trial_data['challenge_memory_rt'] = None

        # feedback message 
        trial_data['feedback_message'] = ""
        
        trial_list.append(trial_data)
        win.flip()
        core.wait(0.3)
    return trial_list


# FILLER TASK 

def run_filler_task(win, duration=10):  #duration
    """
    dot judgment filler task
    In each trial, two boxes with red dots are presented.
    The participant presses 'F' or 'J' to indicate which box has more dots.
    """
    import random
    from psychopy import visual, core, event
    
    
    if duration < 5:
        print(f"WARNING: Duration {duration}s is too short! Setting to 120 seconds (2 minutes)")
        duration = 10  

    old_units = win.units
    win.setUnits("norm")
    
    print(f"Starting filler task... Duration set to {duration} seconds")

    filler_instructions = visual.TextStim(
        win,
        text="You will see 2 boxes with number of dots\n\nThe boxes will be displayed only for 1 sec\nJudge which box has more dots.\n\nPress SPACE to begin.",
        pos=(0, 0), height=0.08, color="white"
    )
    filler_instructions.draw()
    win.flip()

    event.clearEvents()  
    key = event.waitKeys(keyList=["space", "escape"])
    if key and key[0] == "escape":
        win.close()
        core.quit()

    global_clock = core.Clock()
    global_clock.reset()  # Start the clock
    trial_count = 0
    
    # Main task loop - runs until duration is reached
    # Only exit early if very little time remains (< 3 seconds)
    while global_clock.getTime() < (duration - 3):
        trial_count += 1
        trial_start_time = global_clock.getTime()
        remaining_time = duration - trial_start_time
        
        print(f"Trial {trial_count}: {trial_start_time:.2f}s elapsed, {remaining_time:.2f}s remaining")
            
        keys = event.getKeys(keyList=["escape"])
        if "escape" in keys:
            win.close()
            core.quit()
            
        # Create stimuli 
        left_dots = random.randint(10, 30)
        right_dots = random.randint(10, 30)
        
        box_width, box_height = 0.8, 1.6  

        # boxes
        left_box = visual.Rect(win, width=box_width, height=box_height, pos=(-0.5, 0),
                              lineColor="white", fillColor=None, lineWidth=2)
        right_box = visual.Rect(win, width=box_width, height=box_height, pos=(0.5, 0),
                               lineColor="white", fillColor=None, lineWidth=2)
        
        # dot positions 
        left_x_min = -0.8
        left_x_max = -0.2
        left_y_min = -0.7
        left_y_max = 0.7
        
        right_x_min = 0.2
        right_x_max = 0.8
        right_y_min = -0.7
        right_y_max = 0.7

        # Draw boxes first
        left_box.draw()
        right_box.draw()
        
        # Draw left dots
        for _ in range(left_dots):
            x = random.uniform(left_x_min, left_x_max)
            y = random.uniform(left_y_min, left_y_max)
            dot = visual.Circle(win, radius=0.02, pos=(x, y),
                               fillColor="red", lineColor=None)
            dot.draw()
            
        # Draw right dots
        for _ in range(right_dots):
            x = random.uniform(right_x_min, right_x_max)
            y = random.uniform(right_y_min, right_y_max)
            dot = visual.Circle(win, radius=0.02, pos=(x, y),
                               fillColor="red", lineColor=None)
            dot.draw()

        win.flip()
        core.wait(0.75)
        win.flip()
        core.wait(0.3)

        # Show question and response options
        question = visual.TextStim(win, text="Which box has more dots?", pos=(0, -0.1),
                                 height=0.07, color="white")
        left_text = visual.TextStim(win, text="Press 'A' for left", pos=(-0.7, -0.3),
                                  height=0.07, color="white")
        right_text = visual.TextStim(win, text="Press 'L' for right", pos=(0.7, -0.3),
                                   height=0.07, color="white")
        question.draw()
        left_text.draw()
        right_text.draw()
        win.flip()

        # Calculate how much time is left for this trial's response
        response_time_limit = min(2.0, duration - global_clock.getTime())
        
        # Only wait for a response if we have time
        if response_time_limit > 0.1:  # At least 100ms to respond
            event.clearEvents()  
            keys = event.waitKeys(keyList=["a", "l", "escape"], maxWait=response_time_limit)
            
            if keys:
                response = keys[0]
                if response == "escape":
                    win.close()
                    core.quit()
                else:
                    correct_response = "a" if left_dots > right_dots else "l"
                    feedback = "Correct!" if response == correct_response else "Incorrect!"
                
                # Show feedback, but check time remaining first
                if global_clock.getTime() < duration - 1.5:
                    feedback_text = visual.TextStim(win, text=feedback, pos=(0, 0),
                                                  height=0.1, color="yellow")
                    feedback_text.draw()
                    win.flip()
                    
                    # Show feedback for a maximum of 1.5 seconds
                    feedback_time = min(1.5, duration - global_clock.getTime() - 0.1)
                    if feedback_time > 0:
                        core.wait(feedback_time)
            
        # Brief pause between trials if time allows
        remaining_time = duration - global_clock.getTime()
        if remaining_time > 0.5:
            core.wait(0.2)
    
    final_time = global_clock.getTime()
    print(f"Filler task completed: {final_time:.2f} seconds, {trial_count} trials")
    win.setUnits(old_units)
    win.flip()
    print("Exiting filler task function")

# CHALLENGE PHASE

def run_challenge_phase(win, slider, rt_clock, trial_list):
    """
    Processes the trial_list in presentation order after pre-filtering
    Pre-filtering:
      - Skip any trial where the participant pressed 'y' but trial['y_n'] is 'n'
      - Skip any trial where the participant pressed 'n' but trial['old_new'] is 'new'
      - If the participant pressed 'n':
           *feedback "You correctly rejected the word" (in green) with a SPACE prompt
    """
    # feedback instru.
    feedback_instr = visual.TextStim(
        win=win,
        text="Here is your Feedback on your answers\n\nOur memories are prone to distortions and false memories. Check how good is your memory\n\nYou're required to give the ratings again for wrong responses\n\nPress SPACE to continue",
        font='Arial',
        height=40,
        color='white',
        wrapWidth=1500
    )
    feedback_instr.draw()
    win.flip()
    key = event.waitKeys(keyList=['space', 'escape'])
    if key and key[0] == 'escape':
        win.close()
        core.quit()

    # Pre-filter the trial list
    filtered_trials = [trial for trial in trial_list 
                       if not (trial['recognition_response'] == 'n' and trial['y_n'].strip().lower() == 'y')]


    # Sort filtered trials by presentation order.
    sorted_trials = sorted(filtered_trials, key=lambda x: x['presentation_order'])
    recognized_counter = 0  # Count recognized ('y') responses only.

    for trial in sorted_trials:
        # Clear the window at the start of each trial.
        win.flip()
        word_str = trial['word']
        
        # Display the word in white at the top.
        word_stim = visual.TextStim(
            win=win,
            text=word_str,
            font='Arial',
            height=48,
            color='white',
            wrapWidth=1500,
            pos=(0, 100)
        )
        word_stim.draw()

        if trial['recognition_response'] == 'y':
            recognized_counter += 1
            if recognized_counter % 3 == 0:
                # Challenge trial: display challenge message in red.
                challenge_text = (
                    "Sorry, this answer was incorrect\nThis word was not presented\n\nAgain provide your memory & belief ratings\n\nPress SPACE to continue"
                    
                )
                challenge_stim = visual.TextStim(
                    win=win,
                    text=challenge_text,
                    font='Arial',
                    height=40,
                    color='red',
                    wrapWidth=1500,
                    pos=(0, -100)
                )
                challenge_stim.draw()
                win.flip()
                core.wait(0.8)
                
                key_challenge = event.waitKeys(keyList=['space', 'escape'])
                if key_challenge and key_challenge[0] == 'escape':
                    win.close()
                    core.quit()
                memory_question = (
                    "Do you actually remember that this word has appeared before?\n"
                    "(1 = no memory of the word at all, 8 = clear and complete memory)"
                )
                new_memory_rating, new_memory_rt = get_slider_response(win, memory_question, slider, rt_clock)
                belief_question = (
                    "Do you still believe that this word has appeared before\n"
                    "(regardless of whether you remember or not)?\n\n"
                    "(1 = definitely did not happen, 8 = definitely did happen)"
                )
                new_belief_rating, new_belief_rt = get_slider_response(win, belief_question, slider, rt_clock)
                
                trial['challenge_belief_rating'] = new_belief_rating
                trial['challenge_belief_rt'] = new_belief_rt
                trial['challenge_memory_rating'] = new_memory_rating
                trial['challenge_memory_rt'] = new_memory_rt
                trial['feedback_message'] = "Challenged: This word was not presented. Please rethink and give the ratings."
                win.flip()
            else:
                instr_text = (
                    "Congratulations, your answer was correct\n"
                    "You correctly recognized the word\n\n\n"
                    "Press SPACE to continue"
                )
                instr_stim = visual.TextStim(
                    win=win,
                    text=instr_text,
                    font='Arial',
                    height=36,
                    color='green',
                    wrapWidth=1500,
                    pos=(0, -100)
                )
                instr_stim.draw()
                trial['feedback_message'] = "You correctly recognized the word."
                win.flip()
                event.waitKeys(keyList=['space', 'escape'])
        elif trial['recognition_response'] == 'n':
            instr_text = (
                "Congratulations, your answer was correct\n"
                "You correctly rejected the word\n\n"
                "Press SPACE to continue"
            )
            instr_stim = visual.TextStim(
                win=win,
                text=instr_text,
                font='Arial',
                height=36,
                color='green',
                wrapWidth=1500,
                pos=(0, -100)
            )
            instr_stim.draw()
            trial['feedback_message'] = "You correctly rejected the word."
            win.flip()
            event.waitKeys(keyList=['space', 'escape'])
        core.wait(0.3)

# CSV output

def save_results(trial_list, output_filename):
    sorted_trials = sorted(trial_list, key=lambda x: x['presentation_order'])
    fieldnames = [
        'presentation_order', 'excel_order', 'word', 'Type', 'old_new', 'y_n',
        'recognition_response', 'recognition_rt',
        'belief_rating', 'belief_rt', 'memory_rating', 'memory_rt',
        'challenge_belief_rating', 'challenge_belief_rt',
        'challenge_memory_rating', 'challenge_memory_rt',
        'feedback_message'
    ]
    with open(output_filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for trial in sorted_trials:
            writer.writerow(trial)
    print(f"Results saved to {output_filename}")


# Main fn

def main():
    expInfo = {'Participant': ''}
    dlg = gui.DlgFromDict(dictionary=expInfo, title="Recognition Experiment")
    if not dlg.OK:
        core.quit()

    myMon = monitors.Monitor('myMonitor')
    myMon.setSizePix((1920, 1080))
    myMon.setWidth(53)
    myMon.setDistance(70)
    myMon.frameRate = 120
    myMon.saveMon()

    win = visual.Window(
        size=(1920, 1080),
        fullscr=True,
        color='black',
        units='pix',
        monitor=myMon,
        allowGUI=False
    )
    win.monitorFramePeriod = 1.0 / 120.0

    slider = visual.Slider(
        win=win,
        pos=(0, -150),
        size=(1200, 80),
        labels=["1", "2", "3", "4", "5", "6", "7", "8"],
        ticks=[1, 2, 3, 4, 5, 6, 7, 8],
        style='rating',
        color='White',
        font='Arial',
        labelHeight=20,
        markerColor='Red',
        name='slider'
    )

    rt_clock = core.Clock()

    excel_file = "variables_96.xlsx"
    trial_list = run_recognition_phase(win, slider, rt_clock, excel_file)

    proceed_text = visual.TextStim(
        win=win,
        text="Do you want to proceed to the judgment task?\n\nPress SPACE to continue.",
        font='Arial',
        height=48,
        color='white',
        wrapWidth=1500
    )
    proceed_text.draw()
    win.flip()
    key = event.waitKeys(keyList=['space', 'escape'])
    if key and key[0]=='escape':
        win.close()
        core.quit()

    #   Run filler task 
    run_filler_task(win, duration=95)

    # Run challenge phase 
    run_challenge_phase(win, slider, rt_clock, trial_list)

    output_filename = f"results_{expInfo['Participant']}.csv"
    save_results(trial_list, output_filename)

    end_text = visual.TextStim(
        win=win,
        text="Thank you for participating!\n\nPress any key to exit.",
        font='Arial',
        height=48,
        color='white'
    )
    end_text.draw()
    win.flip()
    event.waitKeys()
    win.close()
    core.quit()

if __name__ == "__main__":
    main()
