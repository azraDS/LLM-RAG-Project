PRODUCT = {
    "title": "Slim Men Blue Jeans",
    "pid": "JEAABC",
    "product_category": "Jeans",
    "category": "Clothing and Accessories",
    "sub_category": "Bottomwear",
    "product_details": "Color: Blue",
}


def test_parse_filters_is_case_insensitive(make_assistant):
    assistant, _ = make_assistant()
    assert assistant._parse_query_filters("Show me JEANS") == {"product_category": "Jeans"}
    assert assistant._parse_query_filters("what is the weather") == {}


def test_parse_filters_matches_category_levels(make_assistant):
    assistant, _ = make_assistant()
    assert assistant._parse_query_filters("anything in footwear")["category"] == "Footwear"
    assert assistant._parse_query_filters("bottomwear please")["sub_category"] == "Bottomwear"


def test_history_is_limited_and_clearable(make_assistant):
    assistant, _ = make_assistant()
    for i in range(5):
        assistant.add_to_history("user", f"msg {i}")
    assert [m["content"] for m in assistant.get_recent_history(2)] == ["msg 3", "msg 4"]
    assert "msg 4" in assistant.format_history_for_context()
    assistant.clear_history()
    assert assistant.format_history_for_context() == ""


def test_classify_intent_lowercases_model_output(make_assistant):
    assistant, openai_client = make_assistant(["Product_Search"])
    assert assistant.classify_intent("I need jeans") == "product_search"
    assert openai_client.calls[0]["model"] == "test-model"


def test_process_query_routes_product_search_with_results(make_assistant):
    assistant, openai_client = make_assistant(["product_search", "Here are jeans"], [PRODUCT])
    assert assistant.process_query("I need jeans") == "Here are jeans"
    prompt = openai_client.calls[1]["messages"][-1]["content"]
    assert "JEAABC" in prompt and "Slim Men Blue Jeans" in prompt


def test_product_search_without_known_category_falls_back_to_catalog_answer(make_assistant):
    assistant, openai_client = make_assistant(["product_search", "We sell jeans and shoes"])
    assert assistant.process_query("something cozy") == "We sell jeans and shoes"
    assert "Footwear" in openai_client.calls[1]["messages"][-1]["content"]


def test_website_question_uses_info_file(make_assistant):
    assistant, openai_client = make_assistant(["website_question", "30 days"])
    assert assistant.process_query("return policy?") == "30 days"
    assert "Returns accepted within 30 days." in openai_client.calls[1]["messages"][-1]["content"]


def test_website_question_without_info_file_apologises(make_assistant, tmp_path):
    assistant, _ = make_assistant(["website_question"])
    assistant.website_info_path = tmp_path / "missing.txt"
    assert "couldn't load the website information" in assistant.process_query("refund?")


def test_unexpected_intent_label_falls_back_to_small_talk(make_assistant):
    assistant, _ = make_assistant(["banana", "Hi there!"])
    assert assistant.process_query("hello") == "Hi there!"


def test_weaviate_failure_returns_friendly_message(make_assistant):
    assistant, _ = make_assistant(["product_search"])

    class Broken:
        def __getattr__(self, name):
            raise RuntimeError("down")

    assistant.weaviate_client = Broken()
    assert "encountered an error" in assistant.process_query("jeans")
