


import json

import requests

input_list = [
    {
        "name": "Reagan Ericson",
        "description": "Reagan Ericson is a student at the University of California, Berkeley. His ambitions include becoming a professional basketball player or a sports commentator. He also wishes to establish a sports academy for underprivileged kids. Reagan comes from a family with two accomplished older brothers who have established high benchmarks for him to follow.",
        "values_deal": "Here are some core personal values that likely guide this person's decisions and actions:\n\n1. **Growth:** This individual values personal development and continuous improvement, evident in their pursuit of running, career goals, and navigating challenges. They seek opportunities to learn, grow, and push their boundaries. \n2. **Resilience:** The ability to overcome difficulties and bounce back from setbacks is a core value.  Their experience with their parents' divorce and their perseverance during COVID demonstrate this. \n3. **Purpose:** This person seeks meaning and fulfillment in their life. They prioritize finding joy and satisfaction in their work and believe it's crucial to align their career with their passions.\n4. **Community:** The importance of connection and support is reflected in their love for spending time with family and friends. They value being part of a group and contributing to the well-being of others.\n5. **Integrity:** The individual seems to prioritize authenticity and being true to themselves. They admire people who are genuine and strive to be honest and ethical in their actions.\n6. **Equality:** This person is passionate about social justice and strives to create a more equitable world. They are particularly concerned about issues like gender representation in STEM fields.\n7. **Health & Wellness:**  Their dedication to running and fitness indicates a strong value placed on physical and mental well-being. They prioritize activities that promote health and a healthy lifestyle.\n\n**Summary:** These values likely influence this individual's life decisions in numerous ways. Their commitment to growth and resilience will likely lead them to seek out challenging opportunities and persevere through adversity.  Their desire for purpose will steer them towards careers that align with their passions and provide fulfillment. Their strong sense of community and equality will likely result in volunteering or activism, while their focus on health and wellness will continue to motivate them to prioritize self-care and healthy habits. Their values will act as a guiding compass, shaping their choices and influencing their actions in pursuit of a meaningful and fulfilling life. \n",
        "mbti": "ISTJ",
        "habbit": "Running is definitely my favorite hobby. I love the feeling of pushing myself physically and mentally. It's a great way to clear my head, stay healthy, and connect with nature. I also enjoy the sense of accomplishment that comes with setting goals and reaching them. ",
        "knowledge": "Calculus concepts (limits, derivatives, integrals), polynomial factoring, complex numbers, logarithmic functions, systems of equations, conic sections, vector analysis, projectile motion, rotational dynamics, thermal physics, electromagnetic induction, nuclear reactions, acid-base equilibria, redox reactions, chemical bonding theories, periodic trends, reaction kinetics, enzyme mechanisms, cellular metabolism, immune response, ecological pyramids, evolutionary biology, genetic mutations, and chromosomal abnormalities."
    },
    {
        "name": "Alexa Caramazza",
        "description": "Alexa Caramazza, 20, studies at San Diego State University. She was the first in her family to graduate from college and holds a degree from San Diego Mesa College. She likes thrifting, beach visits, sustainable fashion, and values time with loved ones. Her family has faced challenges with substance abuse, including her brother, whom she supports. Alexa aspires to help her brother overcome his issues and someday repay her parents by paying off their house.",
        "values_deal": "Here are some core values that likely guide this individual's decisions and actions:\n\n1. **Family:**  This individual prioritizes family and supporting their loved ones. They are proud of their family and their ability to help them, even when facing challenges.\n2. **Personal Growth:** This individual values personal growth and accomplishment. They are proud of their education and their ability to overcome challenges. \n3. **Compassion:** The individual is concerned with social issues like substance abuse and wants to help others.  They admire kindness and support in others.\n4. **Authenticity:** This individual values finding a job they love, even if it doesn't pay as much. They enjoy spending time on activities that bring them joy and relaxation, and they express themselves through thrifting and sustainable fashion. \n5. **Resilience:** The individual demonstrates strength and resilience in the face of family struggles and other challenges. \n6. **Sustainability:** The individual actively seeks out sustainable clothing options and values giving old items new life through thrifting. \n\n**Summary:** This individual's values suggest they are likely to make decisions that prioritize family, personal growth, and helping others.  They seek out experiences and opportunities that align with their interests and passions and value authenticity and resilience. Their concern for sustainability might also influence their choices in areas like shopping and leisure activities. \n",
        "mbti": "ESFP",
        "habbit": "My favorite hobby is thrifting. I love finding unique and vintage pieces of clothing and accessories.  It's so much fun to give old items a new life and express my personal style. ",
        "knowledge": "Integration techniques, differential equations, geometric proofs, coordinate geometry, infinite series, rational functions, fluid mechanics, wave optics, quantum mechanics, thermodynamics principles, electrochemistry, chemical kinetics, spectroscopy, molecular geometry, advanced organic synthesis, biochemistry pathways, cellular signaling, plant physiology, animal anatomy, microbial ecology, population genetics, genomics, and biotechnology processes."
    },
    {
        "name": "Anthony Moore",
        "description": "Anthony Moore, a senior at California State University, Fullerton, is driven by a desire to empower individuals. He plans to establish a platform aimed at skill development and boosting confidence. His dream is to evolve into a motivational speaker and writer.",
        "values_deal": "Here are some core values that likely guide this person's decisions and actions:\n\n1. **Achievement:** This individual values hard work and dedication, as evidenced by their pride in their academic achievements and commitment to tutoring. They strive for excellence and likely seek out opportunities for growth and accomplishment.\n2. **Learning:** The individual emphasizes the importance of knowledge and continuous improvement.  Their love for music and their pursuit of computer science demonstrate a desire for intellectual stimulation and a willingness to expand their horizons.\n3. **Social Justice:** This individual is deeply concerned about equity and inclusivity, particularly in the tech industry. They actively seek to make a positive impact on the world and are likely drawn to careers that align with these values.\n4. **Passion:**  This person prioritizes pursuing activities that they genuinely enjoy and find fulfilling.  They value the ability to express themselves creatively through music and seek out opportunities that spark their enthusiasm.\n5. **Empathy:**  The individual values compassion and actively seeks to help others.  Their dedication to tutoring and their admiration for those who are supportive and helpful point to a strong desire to contribute positively to the lives of others.\n6. **Growth Mindset:** This person values self-improvement and open-mindedness. Their admiration for those who are willing to learn and constantly striving to better themselves suggests a commitment to personal growth and development.\n\n**Summary:**  This individual's values likely influence their life decisions and behaviors in a number of ways. They are likely to prioritize careers that offer opportunities for growth, intellectual stimulation, and a chance to make a positive impact.  They will seek out relationships with individuals who share their values of empathy, support, and personal growth.  Their decision-making will likely be guided by a desire to create a fulfilling and meaningful life that aligns with their core beliefs.  \n",
        "mbti": "ENTP",
        "habbit": "My favorite hobby is music.  I enjoy listening to a wide range of genres and playing the bass guitar. Music allows me to express myself creatively and connect with others on a deeper level. ",
        "knowledge": "Multivariable calculus, complex integral calculus, linear algebra, abstract algebra, advanced trigonometry, statistical analysis, mechanical advantage and simple machines, fluid statics and dynamics, special relativity, nuclear physics, atomic structure and orbitals, chemical bonding and intermolecular forces, entropy and Gibbs free energy, titrations , industrial chemistry processes, stereochemistry, hydrocarbon reactions, cellular organelles and their functions, photosynthesis and cellular respiration, animal development and embryology, virus structure and replication, Hardy-Weinberg equilibrium, and genetic engineering techniques.\n"
    },
    {
        "name": "Lili Tombe",
        "description": "Lili Tombe, an 18-year-old incoming freshman at the University of California, Irvine, dreams of becoming a civil rights lawyer. She plans to major in Political Science at UCI to further her goal of earning a law degree. Grew up in a predominantly white neighborhood with few people who looked like her or understood her struggles. She has reconnected with her culture and wants to contribute to her community that has given her so much.",
        "values_deal": "Here are some core personal values that likely guide this person's decisions and actions:\n\n1. **Growth & Achievement:** This person values personal growth and overcoming challenges. Their pride in overcoming academic struggles demonstrates a commitment to self-improvement and a belief in their own potential.\n2. **Authenticity & Self-Expression:** Embracing their identity and finding their voice are important to this person. They value being true to themselves and expressing their unique qualities.\n3. **Social Justice & Equality:**  This person is deeply concerned about discrimination and injustice against marginalized groups. Their desire to use their career in law to fight for those who have been unjustly treated shows a strong commitment to social justice and equality.\n4. **Purpose & Fulfillment:** This person prioritizes finding fulfillment and joy in their work over financial gain. They believe that making a difference and contributing to the world is more important than material wealth.\n5. **Compassion & Empathy:**  They admire kindness, compassion, and empathy in others and likely embody these qualities themselves. This suggests a desire to connect with others on a deeper level and make a positive impact on their lives.\n6. **Creativity & Self-Reflection:**  This person finds solace and self-expression in writing poetry and journaling. They value creative outlets and introspection as ways to process their thoughts and emotions. \n7. **Nature & Mindfulness:**  Connecting with the natural world is important for this person's well-being. This suggests a value for mindfulness,  peace, and a connection to something larger than themselves.\n\n**Summary:**\n\nThis person's values are likely to influence their life decisions and behaviors in several ways:\n\n* **Career choices:** They will likely seek careers that align with their values of social justice, creativity, and making a difference. They may be drawn to fields like law, social work, or the arts, where they can use their skills to help others and advocate for change. \n* **Personal relationships:**  They will likely be drawn to people who share their values of compassion, empathy, and authenticity. They will prioritize fostering genuine connections and building supportive relationships.\n* **Lifestyle choices:** They will likely prioritize activities that align with their values of growth, self-expression, and connecting with nature. They may participate in volunteering, creative pursuits, and outdoor activities. \n* **Overall life approach:** This person's values suggest a strong commitment to personal growth, making a positive impact on the world, and living a life that is both meaningful and fulfilling. \n",
        "mbti": "INFP",
        "habbit": "Writing poetry is my favorite hobby. It's a way for me to express my thoughts and emotions, and I find it incredibly therapeutic. It allows me to explore my creativity and connect with others on a deeper level. ",
        "knowledge": "Graphing complex functions, solving higher-order differential equations, understanding real and complex analysis, manipulating matrices and determinants, mastering combinatorics and probability theory, applying the principles of gravitational forces and orbital mechanics, interpreting electromagnetic fields and wave equations, exploring the quantum nature of particles, deciphering advanced thermodynamic cycles, performing complex chemical synthesis, analyzing reaction rates and mechanisms, identifying and characterizing organic compounds through spectroscopy, comprehending the detailed processes of cellular division, unraveling the complexities of neural communication, studying the intricacies of ecological systems and biodiversity, decoding the molecular basis of inheritance and genetic disorders, and navigating the ethics and procedures of biotechnological advancements."
    },
    {
        "name": "Adrina Daniel",
        "description": "Audrina Alexis Daniel, 20, attends San Diego State University. She aims to write a self-help book, obtain a master's in elementary education, become a teacher, and build a wonderful family. Her father has been supportive, her mother dealt with addiction and tragically passed away, and she has a younger sister.",
        "values_deal": "Here are some core personal values that likely guide this individual's decisions and actions:\n\n1. **Resilience:** This person demonstrates a strong ability to overcome challenges and adversity, finding strength and learning from difficult experiences. They actively choose to face their pain instead of being defined by it, showcasing resilience in their approach to life.\n\n2. **Authenticity:**  They emphasize staying true to themselves and their values, even if it means going against societal pressures or taking a less conventional path. This highlights a commitment to living a life aligned with their personal beliefs and goals.\n\n3. **Passion:** They prioritize pursuing their passions, even when it requires effort and dedication.  This value manifests in their pursuit of both creative endeavors (writing) and their educational goals, reflecting a commitment to finding meaning and fulfillment in their pursuits.\n\n4. **Empathy and Compassion:** The individual expresses concern for others' well-being, especially when it comes to mental health.  This concern reflects a deep sense of empathy and compassion for those struggling, which may influence their choices in social and professional spheres.\n\n5. **Purpose:**  They value a sense of purpose in their work and life, choosing fulfillment over financial gain. This aligns with their desire to contribute to something they believe in, emphasizing the importance of a meaningful and impactful life.\n\n6. **Personal Growth:**  This individual is committed to continuous learning and development, as seen in their dedication to their education and their pursuit of creative outlets. This value suggests a desire for self-improvement and a commitment to personal growth.\n\n**How these values might influence life decisions and behaviors:**\n\nThis person's values likely drive them towards seeking out meaningful and fulfilling experiences, prioritizing personal growth and contributing to something larger than themselves. They may be drawn to careers that align with their passions and allow for creative expression, while also considering their impact on society. They might prioritize relationships with people who share their values of authenticity, empathy, and resilience.  They are likely to be active in their community and advocate for issues they care about, especially those related to mental well-being. Overall, their values are likely to guide them towards a life filled with purpose, passion, and a strong sense of personal fulfillment. \n",
        "mbti": "INFJ",
        "habbit": "My favorite hobby is definitely writing. I love the process of creating stories and exploring different perspectives.  It's a way for me to express myself and connect with others on a deeper level.",
        "knowledge": "Calculus limits, derivatives, vector operations, algebraic equations, inequalities, integrals, thermodynamics principles, quantum mechanics, redox reactions, electrochemistry, atomic structure, periodic trends, chemical bonding theories, cellular respiration, photosynthesis, ecosystems, population dynamics, molecular biology, gene expression, regulation."
    },
    {
        "name": "Mallory Asis",
        "description": "Mallory Asis, a student at UCLA, is a committed long-distance runner with dreams of joining the national team and participating in the Olympics. Alongside her athletic pursuits, she plans to raise awareness for mental health and intends to work in sports medicine. Coming from a family of educators and community servants, she has a twin brother who loves running and a younger sister interested in art. Mallory is motivated by her family's values to make a positive impact on others.",
        "values_deal": "Here are some core personal values that likely guide this person's decisions and actions:\n\n1. **Resilience:**  The individual has overcome significant challenges in their life, demonstrating a strong ability to bounce back from adversity. This value likely drives them to persevere through difficult times and approach life with a sense of determination.\n2. **Compassion:**  The person's concern for social issues like sexual violence, coupled with their desire to help others through their writing, points to a deep sense of compassion. They likely prioritize helping those in need and contributing to a more just and equitable world.\n3. **Authenticity:**  The individual values finding joy and fulfillment in their work, suggesting a preference for living a life that aligns with their true self. This value might lead them to make career choices that prioritize personal satisfaction over financial gain.\n4. **Creativity:**  The person expresses themselves through various creative outlets, highlighting the importance of self-expression and artistic exploration in their life. This value could motivate them to pursue creative hobbies and endeavors, enriching their personal experience and fostering their unique talents.\n5. **Integrity:** The person's commitment to tackling sensitive topics like juvenile sex offenders demonstrates a willingness to confront difficult truths and advocate for social change. This value suggests they prioritize moral conduct and strive to live in accordance with their beliefs.\n6. **Personal Growth:** The individual's passion for running, along with their desire to challenge themselves physically and mentally, points to a strong drive for personal growth and self-improvement. This value could manifest in their commitment to pushing their limits, learning new skills, and constantly striving to become a better version of themselves.\n\n**Summary:** These values might influence the person's life decisions and behaviors by shaping their career choices, relationships, and overall approach to life. They might prioritize careers that align with their passions and allow them to make a positive impact on the world. They may seek out relationships with people who share their values and strive to create a life that is both meaningful and fulfilling. Their commitment to personal growth could lead them to continuously challenge themselves and learn from new experiences. \n",
        "mbti": "INFJ",
        "habbit": "I'm passionate about running.  It's more than just a hobby for me; it's a way to challenge myself physically and mentally, and it helps me to connect with my inner strength. I'm excited about getting back into running and even exploring ultra marathons!",
        "knowledge": "Trigonometric identities, logarithmic functions, complex numbers, probability distributions, statistical inference, kinematic equations, Newton’s laws, force diagrams, energy conservation, momentum conservation, electrical circuits, wave properties, chemical equations, stoichiometry, organic chemistry nomenclature, cell organelles, DNA structure, protein function, genetic inheritance patterns, Punnett squares, biological taxonomy, ecological interactions."
    },
    {
        "name": "Mauro Gutirrez",
        "description": "Mauro Gutiérrez, a senior at a local high school in San Diego, aspires to become a software engineer and attend a prestigious university such as MIT or Stanford. He is also passionate about traveling and exploring various cultures around the globe. Mauro comes from a family that includes his parents, who manage a small business, and a brother who is currently in his first year of college.",
        "values_deal": "Here are some core personal values that likely guide this individual's decisions and actions:\n\n1. **Growth and Adaptability:**  This individual demonstrates a strong desire to learn and adapt to new environments, as evidenced by their pride in excelling in new situations. This value likely drives them to seek out challenges and opportunities for personal development.\n2. **Empathy and Compassion:**  The concern for lack of understanding and empathy in the world highlights a strong value for human connection and understanding. This individual likely prioritizes building positive relationships and fostering a sense of community.\n3. **Authenticity and Fulfillment:**  Choosing a lower-paying job they love demonstrates a commitment to living a life that aligns with their values and passions. This person likely prioritizes personal fulfillment over material wealth.\n4. **Social Connection and Joy:**  The enjoyment of spending time with friends and family, exploring new places, and making people laugh reveals a strong value for social connection and finding joy in life. This individual likely seeks out experiences that create positive memories and strengthen relationships. \n5. **Honesty and Loyalty:**  Admiration for honesty, loyalty, and kindness in others suggests a strong personal commitment to building trust and genuine relationships. This person likely values authenticity and integrity in their interactions with others.\n\n**Summary:**\n\nThis individual's values likely influence their life decisions and behaviors in a number of ways. They are likely to seek out opportunities for growth and development, prioritize building meaningful relationships, and make choices that align with their passions and values. They may choose careers that offer personal fulfillment and social impact over purely financial gain. They are likely to be a supportive and loyal friend, and actively seek to contribute to a more compassionate and understanding world. \n",
        "mbti": "ENFJ",
        "habbit": "I enjoy making people laugh and bringing joy to others. I find humor to be a great way to connect with people and make life more enjoyable. I also appreciate spending time outdoors and experiencing new places.",
        "knowledge": "Algebraic fractions, quadratic equations, systems of equations, exponential growth, logarithmic scales, permutations and combinations, geometric proofs, circular motion, gravitational forces, fluid mechanics, heat transfer, nuclear reactions, acid-base equilibria, chemical kinetics, polymer structures, biochemistry pathways, cell division, immune response, evolutionary biology, genetic mutations, ecological pyramids.\n"
    },
    {
        "name": "Maria Noriega",
        "description": "Maria Noriega is a student at a local community college with ambitions to transfer to a university for a business administration degree. She dreams of starting her own business and traveling globally. Raised by her grandmother following the loss of her parents at a young age, Maria values her close familial ties.",
        "values_deal": "Here are some potential core values based on Maria's responses:\n\n1. **Personal Growth:** Maria values continuous learning and improvement, evident in her pursuit of higher education and her desire to overcome challenges. This value motivates her to strive for self-development and seek out new experiences.\n2. **Fulfillment:**  Maria prioritizes finding satisfaction and meaning in her work, emphasizing the importance of enjoying what she does. This value guides her career choices, making her less likely to prioritize financial gain over personal fulfillment.\n3. **Social Justice:**  Maria is deeply concerned with inequality and strives for a more equitable world. This value likely motivates her to advocate for marginalized groups, especially women in STEM, and potentially influences her career choices towards social impact.\n4. **Wellness:**  Maria prioritizes her physical and mental health, demonstrating a strong interest in nutrition, exercise, and skincare. This value informs her lifestyle choices and motivates her to prioritize self-care and wellbeing.\n5. **Compassion:** Maria admires kindness and empathy in others, suggesting a strong sense of empathy and a desire to help others. This value likely influences her interactions with others and potentially motivates her to volunteer or engage in charitable work.\n6. **Determination:**  Maria values persistence and resilience, evident in her overcoming challenges during her studies. This value likely motivates her to pursue her goals and persevere even in the face of adversity.\n\n**Summary of Influence**\n\nThese values suggest that Maria is likely to make decisions that prioritize personal growth, fulfillment, and social good. She may be drawn to careers that offer opportunities to learn and grow, contribute to a cause she believes in, and allow her to be a positive force for change.  Her lifestyle choices are likely to be influenced by her focus on wellness and her desire to live a balanced and fulfilling life. She is likely to be a supportive friend and family member who is committed to creating a more just and equitable world. \n",
        "mbti": "ENFJ",
        "habbit": "I'm really passionate about health and wellness. I love learning about nutrition, exercise, and the human body. I'm also fascinated by the beauty industry and the science behind skincare and cosmetics.",
        "knowledge": "Linear programming, differential equations, complex integration, combinatorial logic, statistical variance, gravitational potential energy, angular momentum, electromagnetic induction, atomic spectra, molecular geometry, chemical equilibrium, titration analysis, hydrocarbon isomers, enzyme kinetics, plant anatomy, animal physiology, genetic engineering, cladistics, environmental science, biogeochemical cycles.\n"
    }
]

for i in input_list:
    url = "http://127.0.0.1:5001/backend-api/v1/create_model_person"

    payload = json.dumps(i)
    headers = {
      'Authorization': 'Bearer b10dd914-d28d-10b4-11c4-3a8b61d8a77f',
      'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)
