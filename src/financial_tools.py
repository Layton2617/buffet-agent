import numpy as np
from typing import Dict, List, Optional

class FinancialTools:
    
    @staticmethod
    def calculate_dcf(free_cash_flows: List[float], 
                     terminal_growth_rate: float = 0.025,
                     discount_rate: float = 0.10,
                     terminal_year: int = 5) -> Dict:
        
        if not free_cash_flows or len(free_cash_flows) < terminal_year:
            return {"error": "Insufficient cash flow data"}
        
        try:
            projected_fcf = free_cash_flows[:terminal_year]
            
            terminal_value = projected_fcf[-1] * (1 + terminal_growth_rate) / (discount_rate - terminal_growth_rate)
            
            present_values = []
            for i, fcf in enumerate(projected_fcf):
                pv = fcf / ((1 + discount_rate) ** (i + 1))
                present_values.append(pv)
            
            terminal_pv = terminal_value / ((1 + discount_rate) ** terminal_year)
            
            enterprise_value = sum(present_values) + terminal_pv
            
            return {
                "enterprise_value": round(enterprise_value, 2),
                "terminal_value": round(terminal_value, 2),
                "terminal_pv": round(terminal_pv, 2),
                "present_values": [round(pv, 2) for pv in present_values],
                "discount_rate": discount_rate,
                "terminal_growth_rate": terminal_growth_rate
            }
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def analyze_pe_ratio(current_pe: float, 
                        industry_avg_pe: float,
                        historical_pe_range: List[float],
                        earnings_growth_rate: float) -> Dict:
        
        try:
            if not historical_pe_range or len(historical_pe_range) < 2:
                historical_pe_range = [15, 25]
            
            historical_min = min(historical_pe_range)
            historical_max = max(historical_pe_range)
            historical_avg = sum(historical_pe_range) / len(historical_pe_range)
            
            peg_ratio = current_pe / (earnings_growth_rate * 100) if earnings_growth_rate > 0 else None
            
            valuation_signal = "NEUTRAL"
            if current_pe < historical_min * 0.8:
                valuation_signal = "UNDERVALUED"
            elif current_pe > historical_max * 1.2:
                valuation_signal = "OVERVALUED"
            elif current_pe < industry_avg_pe * 0.9:
                valuation_signal = "ATTRACTIVE"
            elif current_pe > industry_avg_pe * 1.1:
                valuation_signal = "EXPENSIVE"
            
            return {
                "current_pe": current_pe,
                "industry_avg_pe": industry_avg_pe,
                "historical_min": historical_min,
                "historical_max": historical_max,
                "historical_avg": round(historical_avg, 2),
                "peg_ratio": round(peg_ratio, 2) if peg_ratio else None,
                "valuation_signal": valuation_signal,
                "relative_to_industry": round((current_pe / industry_avg_pe - 1) * 100, 1),
                "relative_to_history": round((current_pe / historical_avg - 1) * 100, 1)
            }
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def calculate_margin_of_safety(intrinsic_value: float,
                                 current_price: float,
                                 minimum_margin: float = 0.20) -> Dict:
        
        try:
            if current_price <= 0 or intrinsic_value <= 0:
                return {"error": "Invalid price or intrinsic value"}
            
            margin_of_safety = (intrinsic_value - current_price) / intrinsic_value
            
            safety_rating = "DANGEROUS"
            if margin_of_safety >= minimum_margin:
                safety_rating = "SAFE"
            elif margin_of_safety >= minimum_margin * 0.5:
                safety_rating = "MODERATE"
            elif margin_of_safety >= 0:
                safety_rating = "MINIMAL"
            
            upside_potential = (intrinsic_value / current_price - 1) * 100
            
            recommendation = "AVOID"
            if margin_of_safety >= minimum_margin:
                recommendation = "BUY"
            elif margin_of_safety >= minimum_margin * 0.5:
                recommendation = "CONSIDER"
            elif margin_of_safety >= 0:
                recommendation = "HOLD"
            
            return {
                "intrinsic_value": intrinsic_value,
                "current_price": current_price,
                "margin_of_safety": round(margin_of_safety * 100, 2),
                "minimum_margin": round(minimum_margin * 100, 2),
                "safety_rating": safety_rating,
                "upside_potential": round(upside_potential, 2),
                "recommendation": recommendation,
                "price_to_value_ratio": round(current_price / intrinsic_value, 3)
            }
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def calculate_vwap(prices: List[float], volumes: List[float]) -> Dict:
        
        try:
            if len(prices) != len(volumes) or not prices:
                return {"error": "Invalid price or volume data"}
            
            total_volume = sum(volumes)
            if total_volume == 0:
                return {"error": "Zero total volume"}
            
            weighted_sum = sum(p * v for p, v in zip(prices, volumes))
            vwap = weighted_sum / total_volume
            
            current_price = prices[-1]
            price_vs_vwap = (current_price / vwap - 1) * 100
            
            signal = "NEUTRAL"
            if price_vs_vwap < -2:
                signal = "OVERSOLD"
            elif price_vs_vwap > 2:
                signal = "OVERBOUGHT"
            elif price_vs_vwap < -1:
                signal = "BELOW_VWAP"
            elif price_vs_vwap > 1:
                signal = "ABOVE_VWAP"
            
            return {
                "vwap": round(vwap, 2),
                "current_price": current_price,
                "price_vs_vwap": round(price_vs_vwap, 2),
                "signal": signal,
                "total_volume": total_volume,
                "periods": len(prices)
            }
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def buffett_score(roe: float, debt_to_equity: float, 
                     profit_margin: float, revenue_growth: float,
                     pe_ratio: float) -> Dict:
        
        try:
            score = 0
            factors = {}
            
            if roe >= 15:
                score += 20
                factors["roe"] = "Excellent"
            elif roe >= 10:
                score += 15
                factors["roe"] = "Good"
            elif roe >= 5:
                score += 10
                factors["roe"] = "Average"
            else:
                factors["roe"] = "Poor"
            
            if debt_to_equity <= 0.3:
                score += 20
                factors["debt"] = "Conservative"
            elif debt_to_equity <= 0.6:
                score += 15
                factors["debt"] = "Moderate"
            elif debt_to_equity <= 1.0:
                score += 10
                factors["debt"] = "High"
            else:
                factors["debt"] = "Excessive"
            
            if profit_margin >= 20:
                score += 20
                factors["margin"] = "Excellent"
            elif profit_margin >= 15:
                score += 15
                factors["margin"] = "Good"
            elif profit_margin >= 10:
                score += 10
                factors["margin"] = "Average"
            else:
                factors["margin"] = "Poor"
            
            if revenue_growth >= 10:
                score += 20
                factors["growth"] = "Strong"
            elif revenue_growth >= 5:
                score += 15
                factors["growth"] = "Moderate"
            elif revenue_growth >= 0:
                score += 10
                factors["growth"] = "Slow"
            else:
                factors["growth"] = "Declining"
            
            if pe_ratio <= 15:
                score += 20
                factors["valuation"] = "Cheap"
            elif pe_ratio <= 20:
                score += 15
                factors["valuation"] = "Fair"
            elif pe_ratio <= 25:
                score += 10
                factors["valuation"] = "Expensive"
            else:
                factors["valuation"] = "Overvalued"
            
            rating = "AVOID"
            if score >= 80:
                rating = "STRONG_BUY"
            elif score >= 70:
                rating = "BUY"
            elif score >= 60:
                rating = "HOLD"
            elif score >= 50:
                rating = "WEAK_HOLD"
            
            return {
                "buffett_score": score,
                "rating": rating,
                "factors": factors,
                "metrics": {
                    "roe": roe,
                    "debt_to_equity": debt_to_equity,
                    "profit_margin": profit_margin,
                    "revenue_growth": revenue_growth,
                    "pe_ratio": pe_ratio
                }
            }
        except Exception as e:
            return {"error": str(e)}

