from polymanager.dashboard import render_actions, render_buy_action


def test_render_buy_action_format():
    opp = {
        "market": "Will Bitcoin reach $80,000 in August?",
        "side": "NO",
        "current_price": 0.850,
        "recommended_investment": 6.00,
        "edge_pp": 4.7,
    }
    text = render_buy_action(opp)
    assert "BUY" in text
    assert "Market: Will Bitcoin reach $80,000 in August?" in text
    assert "Side: NO" in text
    assert "Maximum Entry Price: $0.850" in text
    assert "Investment: $6.00" in text
    # chase ceiling = 0.850 + (4.7/100)/2 = 0.8735
    assert "Do not chase above: $0.873" in text or "Do not chase above: $0.874" in text


def test_render_actions_empty_falls_back_to_no_trade():
    text = render_actions([])
    assert "NO TRADE" in text


def test_render_actions_with_buy_action():
    opp = {
        "market": "Test market",
        "side": "YES",
        "current_price": 0.5,
        "recommended_investment": 5.0,
        "edge_pp": 3.0,
    }
    text = render_actions([render_buy_action(opp)])
    assert "BUY" in text
    assert "NO TRADE" not in text
