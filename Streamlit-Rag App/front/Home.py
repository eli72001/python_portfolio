import streamlit as st
from dotenv import load_dotenv
from frontendhelper import check_collection, check_env_variables
import time
from streamlit.components.v1 import html
from frontendhelper import nav_page, set_bg_hack
from streamlit_extras.stylable_container import stylable_container
from streamlit_extras.app_logo import add_logo

if "setup" not in st.session_state:
    c_1 = time.time()
    load_dotenv()
    check_env_variables()
    c_2 = time.time()
    print(f'LOAD AND CHECK ENV VAR: {c_2 - c_1}')
    d_1 = time.time()
    check_collection() 
    d_2 = time.time()
    print(f'Checking collection: {d_2-d_1}')
    st.session_state.setup = True



st.set_page_config(page_title='KLOE Home', layout='wide')

########## BACKGROUND #################

# st.image(r'ui_assets\hero8v2.png')
set_bg_hack('ui_assets\herobg_dark.png')
add_logo(r'ui_assets\kb_logo_small.png', height=5)
# st.sidebar.image(add_logo(logo_path="ui_assets\Kubrick_Logo_DarkGreen.png", width=80, height=22)) 


############ ARIAL FONT  ##################

st.markdown("""

<style>
body {

    font-family: 'Arial';

}
</style>

""", unsafe_allow_html=True)

########## CONTENT #####################

left, mid, right = st.columns((.5,3,.5))

with left:
    st.write(' ')

with mid:
    st.write('\n\n')
    st.image(r'ui_assets\test2.png')
    btn1, btn2 = st.columns([.5,.5])
    with btn1:
        # with stylable_container(
        #     key="kloe_btn",
        #     # 'button' below in css_styles is the element you will be customizing.
        #     css_styles="""
        #         button { 
        #             background-color: #29D771;
        #             border: none;
        #             color: white;
        #         }
        #         """,
        #     ):
        #         st.write('Retrieve information from your verified sources in seconds. Keep track of your findings with instant annotation on your documents.')
        #         st.button("Go to KLOE Search Portal", use_container_width=True)


            # with stylable_container(
            #     key="container_with_border",
            #     css_styles="""
            #         {
            #             border: 1px solid rgba(49, 51, 63, 0.2);
            #             border-radius: 0.5rem;
            #             padding: calc(1em - 1px)
            #             background-color: #FFFFFF
            #         }
            #         """,
            # ):
            #     st.markdown("This is a container with a border.")   
            if st.button('Go to KLOE Search Portal',use_container_width=True):
                nav_page('KLOE_Search_Portal')
    with btn2:
        if st.button("Go to Annotation Hub",use_container_width=True):
            nav_page('Annotation_Hub')
        # st.markdown('Find all annotated documents from your query sessions, saved automatically and available for download.')

with right:
    st.write(' ')


######### BUTTONS ######################

st.markdown(
    """
<style>
button {
    height: auto;
    padding-top: 20px !important;
    padding-bottom: 20px !important;
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<style>
 
.st-emotion-cache-euc8px {
    font-family: "Arial";
    }
 
</style>
    """,
    unsafe_allow_html = True
)




