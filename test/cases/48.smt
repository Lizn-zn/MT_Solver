(declare-const z Real)
(assert (distinct z 1))
(declare-const y Real)
(assert (distinct y 1))
(declare-const x Real)
(assert (distinct x 1))
(assert (= (* (* x y) z) 1))
(assert (and (< 0 x) (and (< 0 y) (< 0 z))))
(assert (not (>= (+ (+ (/ (^ x 2) (^ (+ x (- 1)) 2)) (/ (^ y 2) (^ (* y (- 1)) 2))) (/ (^ z 2) (^ (+ z (- 1)) 2))) 1)))
(check-sat)
(get-model)
(exit)