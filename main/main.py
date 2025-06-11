"""
main.py is the main seetseeker script.

1. Fetches all available CRNS and stores them in a set.
2. Take a user and their information. Look for which classes they want and which are available. Send them an email to let them know the status.
    # This can be redone to only be sent if their is an available course. If there is then lets delete this CRN from their requested CRN.


"""




from ClassChecker import ClassChecker
course_checker = ClassChecker()

# Write this to read from a .txt file eventually for storage rewrites and general useage.

open_sections = course_checker.run()    #open_sections_set contains type #set

user_info =  { 
                                "email" : "revant.h.patel@gmail.com",
                                "requestedClasses" : [30623,32741,30740,31133,30327] #These should be integers in real script. We need to make sure the user can only put in numbers. if it is found in ALL CRNS
            }

# Returns which classes have been made available and which are still missing
def search_for_user_requested_class( open_sections_set ,user_info):
    open_sections_set = open_sections_set
    email = user_info["email"]
    requested_classes = user_info["requestedClasses"] #List to iterate over and check if is in set

    available_crns = []
    missing_crns = []
    for crn_to_check in requested_classes:
        if str(crn_to_check) in open_sections_set:
            available_crns.append(crn_to_check)
        else:
            missing_crns.append(crn_to_check)

    return available_crns, missing_crns, email


# Sends a user an email on their course search progress
def email_user():
    import smtplib
    from email.message import EmailMessage
    from dotenv import load_dotenv
    import os

    # Load environment variables from .env file
    load_dotenv()

    available_crns, missing_crns, email_reciever = search_for_user_requested_class(open_sections_set=open_sections, user_info=user_info)
    # EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
    # EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

    EMAIL_ADDRESS = "seatseaker@gmail.com"
    EMAIL_PASSWORD = "mmwwjaltepnuwykg"
    msg = EmailMessage()
    msg['Subject'] = 'COURSE_NOTIFICATION'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = email_reciever
    msg.set_content(
        f"""
Hello {email_reciever},

This is a notification from SeatSeeker regarding your requested courses.

Available CRNs:
{', '.join(str(crn) for crn in available_crns) if available_crns else 'None available at this time.'}

Missing CRNs (still unavailable):
{', '.join(str(crn) for crn in missing_crns) if missing_crns else 'All requested courses are available!'}

Thank you for using SeatSeeker!
"""
    )
    

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print(f"EMAIL FAILED TO SEND BECAUSE OF {e}")

def __TEST__():
    email_user()

__TEST__()