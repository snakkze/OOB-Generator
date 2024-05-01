from CTkMessagebox import CTkMessagebox
from tkinter import filedialog
from CTkToolTip import *
import customtkinter
import os
from PIL import Image
import webbrowser
import os
import re
import random
import yaml

class generator:
    def __init__(self):
            self.__coreCheck = True

    @property
    def core_switch(self):
        self.__coreCheck = not self.__coreCheck
        return self.__coreCheck

    def generate_owner_list(self, state_folder, oob_folder_1936):
        self.__owner_list = {}
        self.__owned_provinces_dict = {}

        for file_name in os.listdir(state_folder):
            if file_name.endswith('.txt'):
                file_path = os.path.join(state_folder, file_name)
                with open(file_path, 'r', encoding='utf-8') as state_file:
                    state_content = state_file.read()

                    owner_match = re.search(r'owner\s*=\s*([A-Z]+)', state_content, re.IGNORECASE)
                    province_match = re.search(r'provinces\s*=\s*{([^}]*)}', state_content, re.DOTALL)
                    core_match = re.search(r'add_core_of\s*=\s*([A-Z]+)', state_content, re.IGNORECASE)
                    impassable_match = re.search(r'impassable', state_content)
                    
                    if owner_match and province_match and not impassable_match:
                        owner = owner_match.group(1)
                        if core_match and self.__coreCheck:
                            core_owner = core_match.group(1)
                            if owner != core_owner:
                                continue

                        self.__owner_list.setdefault(owner, {'total_divisions(1936)': 0, 'num_states(1866)': 0})
                        self.__owner_list[owner]['num_states(1866)'] += 1
                        provinces = province_match.group(1).strip().split()
                        self.__owned_provinces_dict.setdefault(owner, []).extend(provinces)

        for file_name in os.listdir(oob_folder_1936):
            if file_name.endswith('_1936.txt'):
                file_path = os.path.join(oob_folder_1936, file_name)
                with open(file_path, 'r', encoding='utf-8') as oob_file:
                    divisions_count = sum(1 for line in oob_file if 'division_template' in line)
                country_tag = file_name.split('_')[0]
                if country_tag in self.__owner_list:
                    self.__owner_list[country_tag]['total_divisions(1936)'] = divisions_count

        return self.__owner_list, self.__owned_provinces_dict
    
    def calculate_divisions_ratio(self, owner_list, provinces_list):
        self.__ratio_list = {}
        self.__average_ratio = 0
        for owner in owner_list:
            if owner_list[owner]['total_divisions(1936)'] > 0:
                ratio = round(owner_list[owner]['total_divisions(1936)'] / len(provinces_list[owner]), 2)
                self.__ratio_list.setdefault(owner, []).extend({ratio})
                self.__average_ratio += ratio

        self.__average_ratio = self.__average_ratio / len(self.__ratio_list)
        return self.__ratio_list, self.__average_ratio
    
    def read_template_config(self, file_path):
        with open(file_path, 'r') as file:
            config = yaml.safe_load(file)
        return config

    def determine_division_templates(self, template_config, provinces_list):
        self.__country_divisions = {}
        for owner, data in provinces_list.items():
            for template_name, template_data in template_config['templates'].items():
                if len(provinces_list[owner]) >= template_data['min_provinces_for_usage']:
                    if owner not in self.__country_divisions:
                        self.__country_divisions[owner] = {}
                    self.__country_divisions[owner][template_name] = template_data['weight']

        return self.__country_divisions
    
    def generate_oob_files(self, template_config ,division_templates, output_folder, owned_provinces_dict, ratio_list, average_ratio, additional_weigth):
        oob_year = template_config['export']['oob_year']
        print(oob_year)
        for owner, templates in division_templates.items():
            oob_file_path = os.path.join(output_folder, f'{owner}_{oob_year}.txt')
            with open(oob_file_path, 'w', encoding='utf-8') as oob_file:
                for template_name, template_data in templates.items():
                    oob_file.write(template_config['templates'][template_name]['template'])      
                oob_file.write('units = {\n')
                if owner in ratio_list:
                    ratio = ratio_list[owner][0]
                else:
                    ratio = average_ratio
                for template_name, template_data in templates.items():
                    weight = template_data
                    num_divisions = round(float(ratio * weight * len(owned_provinces_dict.get(owner, []))) * additional_weigth)
                    for i in range(1, num_divisions + 1):
                        if owned_provinces_dict[owner]:  # Check if owned_provinces is not empty
                            province = random.choice(owned_provinces_dict[owner])
                            oob_file.write(f'\tdivision = {{\n')
                            oob_file.write(f'\t\tdivision_name = {{\n')
                            oob_file.write(f'\t\t\tis_name_ordered = yes\n')
                            oob_file.write(f'\t\t\tname_order = {i}\n')
                            oob_file.write(f'\t\t}}\n')
                            oob_file.write(f'\t\tlocation = {province}\n')
                            oob_file.write(f'\t\tdivision_template = "{template_config["templates"][template_name]["name"]}"\n')
                            oob_file.write(f'\t\tstart_experience_factor = {template_config["templates"][template_name]["start_experience_factor"]}\n')
                            oob_file.write(f'\t}}\n')
                            owned_provinces_dict[owner].remove(province)
                oob_file.write('}\n')

gen = generator()
config = f'{os.getcwd()}\\config.yml'

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.gen = generator()
        self.__additional_weight = 0.5

        def show_error(message):
            CTkMessagebox(title="Error!", message=message, icon="cancel")

        def show_checkmark(message):
            CTkMessagebox(title="Success!", message=message, icon="check")

        def slider_event(addiditionalWeigth):
            self.__additional_weight = addiditionalWeigth
            tooltip_5.configure(message=f'Additional Weigth: {round(addiditionalWeigth, 1)}')
        
        self.__vanilla_folder = 'No folder selected.'
        self.__mod_folder = 'No folder selected.'
        self.__output_folder = 'No folder selected.'

        def browse_vanilla():
            global folder_path
            file = filedialog.askdirectory()
            if os.path.isdir(f'{file}/history/units'):
                self.__vanilla_folder = f'{file}/history/units'
                tooltip_2.configure(message=f'{file}/history/units')
            else:
                show_error(f"Error while setting Mod Directory! Can't seems to find {file}/history/units!")

        def browse_mod():
            global folder_path
            file = filedialog.askdirectory()
            if os.path.isdir(f'{file}/history/states'):
                self.__mod_folder = f'{file}/history/states'
                tooltip_3.configure(message=f'{file}/history/states')
            else:
                show_error(f"Error while setting Mod Directory! Can't seems to find {file}/history/states!")

        def browse_output():
            global folder_path
            file = filedialog.askdirectory()
            if os.path.isdir(file):
                self.__output_folder = file
                tooltip_4.configure(message=file)
            else:
                show_error(f"Error while setting Output Folder! {file} is not a valid Folder!")

        def generate_oob():
            if self.__vanilla_folder != "No folder selected." and self.__mod_folder != "No folder selected." and self.__output_folder != "No folder selected.":
                owner_list, owned_provinces_dict = gen.generate_owner_list(self.__mod_folder, self.__vanilla_folder)
                template_config = gen.read_template_config(config)
                division_templates = gen.determine_division_templates(template_config, owned_provinces_dict)
                ratio_list, average_ratio = gen.calculate_divisions_ratio(owner_list, owned_provinces_dict)
                gen.generate_oob_files(template_config, division_templates, self.__output_folder, owned_provinces_dict, ratio_list, average_ratio, self.__additional_weight)
                show_checkmark(f"Successfully generated OOB to path {self.__output_folder}")
            else:
                show_error("Error while generating OOB, it seems like you forgot to set one of your Paths!")

        self.title("snakkze's OOB Generator")
        self.geometry("700x450")
        self.eval('tk::PlaceWindow . center')
        self.wm_iconbitmap(f'{os.getcwd()}\images\\logo.ico')

        # set grid layout 1x2
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # load images with light and dark mode image
        image_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "images")
        self.logo_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "logo.png")), size=(26, 26))
        self.large_test_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "header_image.png")), size=(500, 150))
        self.image_icon_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "image_icon_light.png")), size=(20, 20))
        self.home_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(image_path, "home_dark.png")),
                                                 dark_image=Image.open(os.path.join(image_path, "home_light.png")), size=(20, 20))
        self.chat_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(image_path, "discord_dark.png")),
                                                 dark_image=Image.open(os.path.join(image_path, "discord_light.png")), size=(20, 20))

        # create navigation frame
        self.navigation_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(4, weight=1)

        self.navigation_frame_label = customtkinter.CTkLabel(self.navigation_frame, text="  OOB Generator", image=self.logo_image,
                                                             compound="left", font=customtkinter.CTkFont(size=15, weight="bold"))
        self.navigation_frame_label.grid(row=0, column=0, padx=20, pady=20)

        self.home_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="Home",
                                                   fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                   image=self.home_image, anchor="w")
        self.home_button.grid(row=1, column=0, sticky="ew")

        self.frame_2_button = customtkinter.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="Our Discord",
                                                      fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                      image=self.chat_image, anchor="w", command=self.frame_2_button_event)
        self.frame_2_button.grid(row=2, column=0, sticky="ew")
        tooltip_1 = CTkToolTip(self.frame_2_button, message="To support me please join my Discord, it is free and ")

        self.appearance_mode_menu = customtkinter.CTkOptionMenu(self.navigation_frame, values=["Light", "Dark", "System"],
                                                                command=self.change_appearance_mode_event)
        self.appearance_mode_menu.grid(row=6, column=0, padx=20, pady=20, sticky="s")

        # create home frame
        self.home_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.home_frame.grid_columnconfigure(0, weight=1)

        self.home_frame_large_image_label = customtkinter.CTkLabel(self.home_frame, text="", image=self.large_test_image)
        self.home_frame_large_image_label.grid(row=0, column=0, padx=20, pady=10)

        self.home_frame_button_1 = customtkinter.CTkButton(self.home_frame, text="Vanilla Path Directory", image=self.image_icon_image, width=350, command=lambda: browse_vanilla())
        self.home_frame_button_1.grid(row=1, column=0, padx=20, pady=10)
        tooltip_2 = CTkToolTip(self.home_frame_button_1, message="No folder selected.")
        self.home_frame_button_2 = customtkinter.CTkButton(self.home_frame, text="Mod Path Directory", image=self.image_icon_image, width=350, command=lambda: browse_mod())
        self.home_frame_button_2.grid(row=2, column=0, padx=20, pady=10)
        tooltip_3 = CTkToolTip(self.home_frame_button_2, message="No folder selected.")
        self.home_frame_button_3 = customtkinter.CTkButton(self.home_frame, text="Output Path Directory", image=self.image_icon_image, width=350, command=lambda: browse_output())
        self.home_frame_button_3.grid(row=3, column=0, padx=20, pady=10)
        tooltip_4 = CTkToolTip(self.home_frame_button_3, message="No folder selected.")

        slider = customtkinter.CTkSlider(master=self.home_frame, from_=0, to=2, width=350, command=slider_event)
        slider.grid(row=4, column=0, padx=20, pady=10)
        slider.set(0.5)
        tooltip_5 = CTkToolTip(slider, message="Additional Weigth: 0.5")

        self.home_frame_button_4 = customtkinter.CTkButton(self.home_frame, width=350, text="Generate OOB", command=generate_oob)
        self.home_frame_button_4.grid(row=5, column=0, padx=20, pady=10)

        self.select_frame_by_name("home")

    def select_frame_by_name(self, name):
        # set button color for selected button
        self.home_button.configure(fg_color=("gray75", "gray25") if name == "home" else "transparent")

        # show selected frame
        if name == "home":
            self.home_frame.grid(row=0, column=1, sticky="nsew")


    def frame_2_button_event(self):
        webbrowser.open('https://discord.gg/QnCHhukPd5')

    def change_appearance_mode_event(self, new_appearance_mode):
        customtkinter.set_appearance_mode(new_appearance_mode)

if __name__ == "__main__":
    app = App()
    app.mainloop()