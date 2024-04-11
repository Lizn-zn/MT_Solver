(declare-const a Real)
(declare-const b Real)

(define-fun f () Real
  (+ (^ a 2) (^ b 2)))

(assert (not (>= f (* (/ 1 2) (^ (+ a b) 2)))))

(check-sat)
(get-model)
(exit)
