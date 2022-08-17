from kanpai import Kanpai

storeReview = Kanpai.Object({
    "lesson": Kanpai.String().required("Please enter your current progress"),
    "comment" : Kanpai.String().required("Please enter your current feedback"),
    "rating" : Kanpai.String().required("Please enter your current rating")
})

