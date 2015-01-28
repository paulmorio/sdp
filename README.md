# Lucky Number Seven

*Murray Crichton, Roy Hotrabhvanon, Teun Kokke, Yiheng Liang, Donal O'Shea, Paul Scherer, Chris Seaton*

Hi my name is

## General Rules to Development
- ***IMPORTANT:*** Please make sure to perform a `git pull` each time before and after you code in order to avoid integration conflicts later on.

- Commit one unit of work each time.

- Each time you pull from the repository, run the tests (when we have them), and run the tests again before you commit.

## Cloning the Repository

Since this is a private repository you will not be able to 'git clone' the repository via https, and thus you will need to use an ssh key that is paired with your account so that you may pull/push the code into the repository. This little guide just explains the commands and what to do so that this can be achieved. (tl;dr copy and paste the commands into your terminal)

### Generating SSH Keys

Simply put SSH keys are a way to identify trusted computers, without involving passwords (except when you authorise an application or process to unlock your key for veification).

If you want the official github explanation (which this is based off of) click [here](https:/help.github.com/articles/generating-ssh-keys/) otherwise just keep on reading.

#### Step 1: Check for already present SSH keys.

Check if there are SSH keys present by using this command 

```ShellSession
ls -la ~/.ssh
```

If you do they should typically listed as follows.

- id_dsa.pub
- id_ecdsa.pub
- id_ed25519.pub
- id_rsa.pub

If not, that is no problem just keep on going.

#### Step 2: Generating a new SSH Key
To generate a new SSH key, you call '''ssh-keygen''' to create an rsa key for you, that is linked to your email address as follows. **Its recommended that you use the email that is linked to your github acccount for the email field, though this is not a requirement.**

```ShellSession
ssh-keygen -t rsa -C "your_email@adress.com"
# Creates a new ssh key using the provided email.
```

You will be asked to provide a passphrase for this ssh key. We advise you to make a strong yet memorable passphrase for this key.

After this is complete you will receive messages that the key was generated successfully. Running 

```ShellSession
ls -la ~/.ssh
```

Should definitely show the files 

- id_rsa
- id_rsa.pub

Created as a result of running the above commands. The id_rsa.pub file will be important in the next section as it contains the your public key (the key that you share with other people/applications to open up secure connection)

Add the key to the ssh-agent.

```ShellSession
# If not already started, start the ssh-agent
eval "$(ssh-agent -s)"
# PID number of the agent will be listed, now add the key to the agent
ssh-add ~/.ssh/id_rsa
```

#### Step 3: Adding the SSH key to your github account.

Open up ~/.ssh/id_rsa.pub with a text editor. Select and copy all of it into your clipboard.

Log into your github account and go into the account setting (symbolised by the cog in top right hand corner). Then find the "SSH KEYS" section on the navigation bar to the left.

Click on the **Add SSH key** 

Give a memorable title that signifies your machine, something like "My DiCE Machine" would work. 

Paste the key in the clipboard into the keyfield.

Add the key, and confirm the action by entering your github password in the dialog box.

#### Step 4: Test your key

Test your key by trying to SSH into github.

```ShellSession
ssh -T git@github.com
```

Say "yes" to connecting, don't worry it wont let you.

You should get a friendly message from GitHub.

#### Step 5: Actually Getting the repository.

After the steps above have been completed you can now git clone the repo into your current working directory (type pwd to find out where you are) and it should create a directory called sdp where all the code is.

```ShellSession
git clone git@github.com:ChrstSea/sdp.git
```

You should be ready to get cracking on the code.

