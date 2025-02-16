import os
from dotenv import load_dotenv
import json
from groq import Groq

load_dotenv('secret.env')  # Load variables from .env

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

def create_chat_completion(content, model):  # New function to create chat completion
    return client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": content,
            }
        ],
        model=model,
    )

def extract_json(text):  # Find content between json and markers
    start_marker = "json"
    end_marker = "```"
    
    try:
        # Find the start of JSON content
        start_index = text.find(start_marker) + len(start_marker)
        
        # Find the end of JSON content
        end_index = text.find(end_marker, start_index)
        
        if start_index == -1 or end_index == -1:
            raise ValueError("JSON markers not found in text")
            
        # Extract the JSON string
        json_str = text[start_index:end_index].strip()
        
        # Parse the JSON string
        return json.loads(json_str)
        
    except Exception as e:
        print(f"Error extracting JSON: {e}")
        return None

def run_groq(content, model):
    chat_completion = create_chat_completion(content, model)
    response_content = chat_completion.choices[0].message.content
    print(response_content)
    json_data = extract_json(response_content)
    print(json.dumps(json_data, indent=2))

# model = "llama-3.1-8b-instant"
if __name__ == "__main__":
    try:
        content = "Using JSON format, Please return the names of people mentioned in the following text and personal information about them: \n\n [{'markdown': '[Skip to content](https://www.regis.org/article?id=11851#content)\n\n## Regis Senior\'s Research Supports Solar System Formation Theory\n\n[![](https://wpnews.regis.org/wp-content/uploads/2021/05/Schubert.jpg)](https://wpnews.regis.org/wp-content/uploads/2021/05/Schubert.jpg)_Marcus Schubert \'21 poses with his research simulation in the Regis Quad._\n\nIn a remarkable achievement for Regis’ Science Research Program (SRP), senior Marcus Schubert ’21 has successfully simulated the collapse of an interstellar dust cloud due to gravity. His research not only corroborates running theories on the formation of our solar system, but supports the hypothesis that such a gravitational collapse can generate other planetary systems.\n\nAccording to the Solar Nebula Theory, our solar system was formed approximately 4.5 billion years ago from a disk of spinning stardust and gas. As gravity pressed on this collection of interstellar material, the build up of pressure caused an expulsion of energy that formed our Sun, planets, and smaller celestial bodies like asteroids, moons, and comets. While a widely accepted theory, any system of more than two bodies cannot be solved mathematically and must be modeled through simulations to prove, which prompted Schubert to pursue this research question throughout his senior year.\n\n“I have experience coding in Python from programming video games and building machine learning models in the past, so I thought it would be a good idea to try out a simulation using gravity,” said Schubert, who was mentored by Regis Physics teacher Dr. Luca Matone throughout his research project. “I find physics interesting since its various laws can be used to explain almost everything we see in the world. It\'s also exciting to know how much we still don\'t know in the field.”\n\nSchubert’s research consisted of developing an algorithm that computed the gravitational forces acting on each interstellar mass due to all the others at a particular moment in time. As this was completed, a code would then calculate the positions each of these masses would take as a result of the forces acting on them. As time was artificially advanced, the forces and positions of the celestial bodies were constantly recomputed, and after several methodological hurdles and some creative thinking, a simulation that proved the Solar Nebula Theory emerged. Schubert’s numerical calculations, organized visually in the below display, not only show that a sudden and sizable collapse in gravity would force space masses to coalesce into a larger body (our Sun), but also that such a collapse would force some bodies (our planets) to fall into this central mass’ gravitational pull.\n\n“Thanks to Marcus’ work, we can see how computer science plays a critical role in the sciences,” Dr. Matone said. “Scientists can test their ideas or hypotheses just to see if they are plausible before embarking on an expensive experiment or costly telescope observation. Well done, Marcus!”\n\nSchubert will be studying Engineering at the University of Michigan next fall, where he hopes to continue exploring the passions for science and research he has developed throughout his time at Regis.\n\n“SRP has been an awesome opportunity for me to explore my research interests,” said Schubert. “I appreciate how I can brainstorm ideas with my mentor and learn loads of invaluable advice. I really learned how to get creative with research. If I have a hypothesis and can think of a way to test it, that\'s research!”\n\nMarcus Schubert \'21 SRP Project: Gravitational Collapse Simulation - YouTube\n\nRegis High School\n\n760 subscribers\n\n[Marcus Schubert \'21 SRP Project: Gravitational Collapse Simulation](https://www.youtube.com/watch?v=u2sAC1-Ihso)\n\nRegis High School\n\nSearch\n\nWatch later\n\nShare\n\nCopy link\n\nInfo\n\nShopping\n\nTap to unmute\n\nIf playback doesn\'t begin shortly, try restarting your device.\n\nMore videos\n\n## More videos\n\nYou\'re signed out\n\nVideos you watch may be added to the TV\'s watch history and influence TV recommendations. To avoid this, cancel and sign in to YouTube on your computer.\n\nCancelConfirm\n\nShare\n\nInclude playlist\n\nAn error occurred while retrieving sharing information. Please try again later.\n\n[Watch on](https://www.youtube.com/watch?v=u2sAC1-Ihso&embeds_referring_euri=https%3A%2F%2Fwww.regis.org%2F)\n\n0:00\n\n0:00 / 0:31•Live\n\n•\n\n[Watch on YouTube]"
        model = "llama-3.3-70b-versatile"    
        run_groq(content, model)
    except Exception as e:
        print(f"Error: {e}")