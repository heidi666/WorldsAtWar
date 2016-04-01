# -*- coding: utf-8 -*-

# Django Imports
from django import template
from django.utils.safestring import mark_safe

# Python Imports
from random import choice

register = template.Library()

def random_quote():

    quotelist = [
     ### Defaults
     "\"Why is my avatar now a nazi flamethrower robot thing\" - rumsod",
     "\"Did you seriously just filter Heil Hitler! to 'Heil Hitler!'?\" - rumsod",
     "\"Soon\" - rumsod",
     "\"Nextfriday™\" - rumsod",
     "\"Should you encounter the enemy, he will be defeated! No quarter will be given! Prisoners will not be taken! " +
        "Whoever falls into your hands is forfeited.\" - Kaiser Willhelm II",
     "\"Every man has a wild beast within him.\" - Friedrich the Great",
     "\"The Earth is the cradle of the mind, but one cannot eternally live in a cradle.\" - Konstantin E. Tsiolkovsky",
     "\"The future will be better tomorrow.\" - Dan Quayle",
     "\"Any sufficiently advanced technology is indistinguishable from magic.\" - Arthur C. Clarke",
     "\"I've seen things you people wouldn't believe. Attack ships on fire off the shoulder of Orion. I watched C-beams glitter in the dark " +
        "near the Tannhauser gate. All those moments will be lost in time... like tears in rain. Time to die.\" - Roy Batty",
      "\"That's one small step for a man, one giant leap for mankind.\" - Neil Armstrong",
     "\"You don't seem to realize my situation here. I will not be stopped. Not by you, or the Confederates, or the Protoss, or anyone. " +
        "I will rule this sector or see it burnt to ashes around me!\" - Arcturus Mengsk",
     "\"Make no mistake, war is coming. With all its glory, and all its horror.\" - Arcturus Mengsk",
     "\"You speak of experience? I have journeyed through the darkness between the most distant stars. " +
        "I have beheld the births of negative-suns and borne witness to the entropy of entire realities...\" - Zeratul",
      "\"Some may question your right to destroy ten billion people. But those who understand realise that you have no right to let them live.\" " +
        "- In Exterminatus Extremis",
     "\"Fate, it seems, is not without a sense of irony.\" - Morpheus",
     "\"A hero need not speak. When he is gone, the world will speak for him.\" - Master Chief",
     "\"If NASA's budgeters could be convinced that there are riches on Mars, we would " +
        "explode overnight to stand on the rim of the Martian abyss.\" - Ray Bradbury",
     "\"Going to the moon is not a matter of physics but of economics.\" - John R. Platt",
     "\"The universe seems neither benign nor hostile, merely indifferent to the concerns of such puny creatures as we are.\" - Carl Sagan",
     "\"I came, I saw, I conquered.\" - Julius Caesar",
     "\"There is no instance of a nation benefitting from prolonged warfare.\" - Sun-Tzu",
     "\"Political power grows out of the barrel of a gun.\" - Mao Zedong",
     "\"Whilst we draw breath, we stand. Whilst we stand, we fight. Whilst we fight, we prevail. Nothing shall stay our wrath.\" - Marneus Calgar",
     "\"There is great pleasure in fighting to gain power, but it is joyless to fight for the sake of maintaining it.\" - Reinhard von Lohengramm",
     "\"An armed society is a polite society. - Robert Heinlein\"",
     "\"The most exciting phrase to hear in science, the one that heralds new discoveries, is not 'Eureka!' but 'That's funny...\" - Issac Asimov",
      "\"So here is us, on the raggedy edge. Don't push me, and I won't push you. Dong le ma?\" - Capt. Malcolm Reynolds",
     "\"The lightning attack is negated in value if the enemy knows which direction it will come from.\" - Jurga Khan",
     "\"Be like smoke - stealing the enemy's sight and breath, but fading to nothingness when he strikes.\" - Cyrus",

     ### Donator
     "\"In this moment, I am euphoric. Not because of any phony god's blessings. But because, I am enlightened by my intelligence.\" - " +
        "<span style=\"color:steelblue;\">Jefferson Spaceship</span>",
     "\"Please remember to look both ways before crossing the street.\" - <span style=\"color:steelblue;\">VenerableSage</span>",
     "\"Glory to The Divine Bush for he protects. When evil flies over head in his bombers, he will not see targets, only bushes. " +
        "When his army of darkness comes to harm you, they shall get lost in the endless bush. The bush loves you, as you love the bush.\" " +
        "- <span style=\"color:steelblue;\">RedArmy BushMan</span>",
     "\"If freedom is short of weapons, we must compensate with willpower.\" - Adolf Hitler - <span style=\"color:steelblue;\">ronizwinter</span>",
     "\"I'd rather betray the whole world than have the whole world betray me.\" - Cao Cao - <span style=\"color:steelblue;\">ICEheaven102</span>",
     "\"Our republican system was meant for a homogeneous people. As long as blacks continue to live with the whites they constitute a threat " +
        "to the national life. Family life may also collapse and the increase of mixed breed bastards may some day challenge the supremacy " +
        "of the white man.\" - Abraham Lincoln - <span style=\"color:steelblue;\">Akeuw</span>",
     "\"Don\'t be retarded.\" - <span style=\"color:steelblue;\">Dickbutts</span>",
     "\"Here we are, on the eleventh of July of the year 1995, in Serbian Srebrenica. On the eve of yet another great Serb holiday we present " +
        "this town as a gift to the Serb nation. The moment has finally arrived that we will have vengeance against the turks in this place.\" " +
        "- Ratko Mladić - <span style=\"color:steelblue;\">Moloko</span>",
     "\"We stand for organized terror - this should be frankly admitted. Terror is an absolute necessity during times of revolution. " +
        "Our aim is to fight against the enemies of the Soviet Government and of the new order of life.\" " +
        "- Felix Dzerzhinsky - <span style=\"color:steelblue;\">Halert</span>",
     "\"African slavery, as it exists in the United States, is a moral, a social, and a political blessing.\" - Jefferson Davis - " +
        "<span style=\"color:steelblue;\">altenland</span>",
     "\"Behold them, conquerors of the world, the toga-clad race of Romans!\" - Augustus - <span style=\"color:steelblue;\">Caesar</span>",
     "\"Rules build up fortifications behind which small minds create satrapies. A perilous state of affairs in the best of times, " +
        "disastrous during crises.\" - Bene Gesserit Coda - <span style=\"color:steelblue;\">Doctor_Hyde</span>",
     "\"The gods envy us. They envy us because we’re mortal, because any moment may be our last. Everything is more beautiful because we’re doomed. " +
        "You will never be lovelier than you are now. We will never be here again.\" - Achilles - <span style=\"color:steelblue;\">S37H</span>",
     "\"Can't SLAMf the BAMF\" - <span style=\"color:steelblue;\">CommyWommy</span>",
     "\"Do you know what 'nemesis' means? A righteous infliction of retribution manifested by an appropriate agent. Personified in this case by an " +
        "'orrible c♥♥♥... me.\" - Brick Top - <span style=\"color:steelblue;\">Grapha</span>",
     "\"Even Speedwagon is afraid!\" - Robert E. O. Speedwagon - <span style=\"color:steelblue;\">Speedwagon</span>",
     "\"Even when your kind appears to triumph, still we rise again. And do you know why? It is because the Order is born of a realization. " +
        "We require no creed. No indoctrination by desperate old men. All we need is that the world be as it is.\" - Haytham Kenway " +
        "- <span style=\"color:steelblue;\">Genghis Khan</span>",
     "\"A true man never dies ... even when he's killed!\" - Kamina - <span style=\"color:steelblue;\">Kamina</span>",
     "\"Don't fuck with the bank.\" - CHOAM - <span style=\"color:steelblue;\">DrKourin</span>",
     "\"Into my heart an air that kills, From yon far country blows:/ What are those blue remembered hills, What spires, what farms are those? " +
        "That is the land of lost content, I see it shining plain, The happy highways where I went, And cannot come again.\" - A E Housman " +
        "- <span style=\"color:steelblue;\">Carpalbone</span>",
     "\"For those of us climbing to the top of the food chain, there can be no mercy. There is but one rule: hunt or be hunted.\" - " +
        "<span style=\"color:steelblue;\">Frank_Underwood</span>",
     "\"THIS IS WAW YOU ABSOLUTE BUTTDOOFUS.\" - The Weederlands - <span style=\"color:steelblue;\">Rampagingwalrus</span>",
     "\"Think of my acts as you will, but do not doubt the reality: the Reclamation has already begun. And we are hopeless to stop it.\" - " +
        "Ur-Didact - <span style=\"color:steelblue;\">Admiral_Parangosky </span>",
     "\"heh\" - RandomWalrus - <span style=\"color:steelblue;\">Ikol</span>",
     "\"ayy lmao\" - <span style=\"color:steelblue;\">Crontical</span>",
     "\"There is no cure for LOVE!\" - Ebola-chan - <span style=\"color:steelblue;\">Mengele-chan</span>",
     "\"Take care not to victimize men both desperate and courageous. Though you rob them of all their gold and silver, " +
        "they still possess swords and shields, helmets and javelins; the plundered keep their weapons.\" - Juvenal - " +
        "<span style=\"color:steelblue;\">Crusader1488</span>",
     "\"Once you get them running, you stay right on top of them, and that way a small force can defeat a large one every time.\" " +
        "- Stonewall Jackson - <span style=\"color:steelblue;\">Reuenthal</span>",
     "\"Like a limb to a man, so are the stars to the New Sun.\" - <span style=\"color:steelblue;\">YeshuaChrist</span>",
     "\"Who is crontical?\" - <span style=\"color:steelblue;\">Slim</span>",
     "\"Lykos is the superior autist\" - Brian of Uberwald - <span style=\"color:steelblue;\">Lykos</span>",
     "\"Dress Horse Best Horse since 2k88\" - <span style=\"color:steelblue;\">Whiskertoes</span>",
     "\"Abou Bakr (may Allah be pleased with him) narrated that the Prophet (Allah's prayer and salvation be upon him) said, " +
        "\'If the people see the wrong being done and do not change it, then Allah will make his punishment common to all.\' " +
        "- <span style=\"color:steelblue;\">Masih_ad-Dajjal</span>",
     "\"Any alliance whose purpose is not the intention to wage war is senseless and useless.\" - Adolf Hitler - " +
        "<span style=\"color:steelblue;\">jadook1</span>",
     "\"Providence shows no mercy to weak nations, but recognizes the right of existence only of sound and strong nations.\" -Adolf Hitler - " +
        "<span style=\"color:steelblue;\">Uther_Fudreim</span>"
    ]

    select = choice(quotelist)

    return mark_safe(select)

register.simple_tag(random_quote)
