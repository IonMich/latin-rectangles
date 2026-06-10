Let

[
\lambda=(\ell_1,\ldots,\ell_c)
]

be the cycle type of the second row permutation (\pi), where (c) is the number of cycles and

[
\ell_1+\cdots+\ell_c=n,\qquad \ell_r\ge 2.
]

For example, if

[
\pi=(1,2,3)(4,5,6,7),
]

then

[
\lambda=(3,4),\quad c=2,\quad n=7.
]

The formula I claimed is

[
\boxed{
E(\ell_1,\ldots,\ell_c)
=======================

\frac12
\sum_{\varepsilon\in{-1,+1}^c}
M_{\left|\varepsilon_1\ell_1+\cdots+\varepsilon_c\ell_c\right|}.
}
]

Here:

* (\varepsilon=(\varepsilon_1,\ldots,\varepsilon_c)) is a **sign vector**.
* The outer sum is over all (2^c) choices of signs.
* For each sign vector, define

[
S(\varepsilon)=\varepsilon_1\ell_1+\cdots+\varepsilon_c\ell_c.
]

* Then the term contributed by that sign vector is

[
M_{|S(\varepsilon)|}.
]

So the formula is more explicitly

[
E(\ell_1,\ldots,\ell_c)
=======================

\frac12
\sum_{\varepsilon_1=\pm1}
\sum_{\varepsilon_2=\pm1}
\cdots
\sum_{\varepsilon_c=\pm1}
M_{\left|\sum_{r=1}^c \varepsilon_r\ell_r\right|}.
]

The index (r) runs over the cycles. The signs (\varepsilon_r) are attached to those same cycles.

---

## Step 1: The rook/matching formula

For a normalized (2\times n) Latin rectangle, the forbidden positions in the third row are

[
(i,i)
\quad\text{and}\quad
(i,\pi(i)).
]

So the third row is a permutation (\sigma\in S_n) such that

[
\sigma(i)\neq i,\qquad \sigma(i)\neq \pi(i)
]

for every column (i).

Equivalently, we count permutation matrices avoiding a forbidden (0)-(1) matrix. By the standard rook formula,

[
E(\pi)
======

\sum_{j=0}^n
(-1)^j r_j (n-j)!,
]

where (r_j) is the number of ways to place (j) nonattacking rooks on forbidden squares.

The forbidden graph decomposes according to the cycles of (\pi). If (\pi) has a cycle of length (\ell), that component is a cycle graph (C_{2\ell}). Therefore, the rook numbers for the full board are obtained by multiplying the matching polynomials of these cycle components.

---

## Step 2: Define the cycle polynomial (q_\ell(t))

For one cycle of length (\ell), define

[
q_\ell(t)
=========

\sum_{j=0}^{\ell}
(-1)^j m_j(C_{2\ell}),t^{\ell-j},
]

where (m_j(C_{2\ell})) is the number of (j)-edge matchings in the cycle graph (C_{2\ell}).

For example, for (\ell=3), the forbidden graph is (C_6). Its matching numbers are

[
m_0=1,\quad m_1=6,\quad m_2=9,\quad m_3=2.
]

So

[
q_3(t)=t^3-6t^2+9t-2.
]

Now define the linear functional

[
F(t^d)=d!,
]

and extend it linearly:

[
F(a_0+a_1t+\cdots+a_nt^n)
=========================

a_0 0!+a_1 1!+\cdots+a_n n!.
]

Then for one cycle,

[
M_\ell:=F(q_\ell)
]

is the one-cycle extension count, i.e. the straight ménage number for cycle length (\ell). For bookkeeping we also allow

[
M_0=F(q_0)=2,\qquad M_1=F(q_1)=-1.
]

Only (M_s) for (s\ge 2) are genuine Latin-extension counts. (M_0) and (M_1) are formal correction terms.

For cycle type (\lambda=(\ell_1,\ldots,\ell_c)), the full extension count is

[
\boxed{
E(\ell_1,\ldots,\ell_c)
=======================

F\left(q_{\ell_1}(t)\cdots q_{\ell_c}(t)\right).
}
]

This is just the rook formula in polynomial form.

---

## Step 3: Chebyshev identity

The crucial identity is

[
q_\ell(t)=2T_\ell\left(\frac{t-2}{2}\right),
]

where (T_\ell) is the Chebyshev polynomial of the first kind.

Equivalently, introduce an auxiliary variable (y) satisfying

[
y+y^{-1}=t-2.
]

Then

[
q_\ell(t)=y^\ell+y^{-\ell}.
]

This is the cleanest way to see the product rule.

For two cycle lengths (a,b),

[
q_a(t)q_b(t)
============

(y^a+y^{-a})(y^b+y^{-b}).
]

Expanding,

[
q_aq_b
======

y^{a+b}+y^{a-b}+y^{-a+b}+y^{-a-b}.
]

Grouping symmetric powers,

[
q_aq_b
======

(y^{a+b}+y^{-(a+b)})
+
(y^{a-b}+y^{-(a-b)}).
]

Therefore

[
\boxed{
q_a(t)q_b(t)=q_{a+b}(t)+q_{|a-b|}(t).
}
]

That absolute value appears because

[
y^{a-b}+y^{-(a-b)}
==================

# y^{|a-b|}+y^{-|a-b|}

q_{|a-b|}(t).
]

---

## Step 4: Product of many (q_{\ell_r})

Now multiply all cycle polynomials:

[
q_{\ell_1}(t)\cdots q_{\ell_c}(t)
=================================

\prod_{r=1}^c
\left(y^{\ell_r}+y^{-\ell_r}\right).
]

When expanding this product, for each cycle length (\ell_r), we choose either (y^{\ell_r}) or (y^{-\ell_r}). That choice is encoded by a sign

[
\varepsilon_r\in{-1,+1}.
]

So one term in the expansion is

[
y^{\varepsilon_1\ell_1+\cdots+\varepsilon_c\ell_c}.
]

Thus

[
q_{\ell_1}\cdots q_{\ell_c}
===========================

\sum_{\varepsilon\in{-1,+1}^c}
y^{S(\varepsilon)},
]

where

[
S(\varepsilon)
==============

\sum_{r=1}^c \varepsilon_r\ell_r.
]

But (q_s(t)=y^s+y^{-s}), so we want to rewrite the sum of powers of (y) in terms of (q_s)'s. Observe that the sign vector (-\varepsilon) gives

[
S(-\varepsilon)=-S(\varepsilon).
]

Therefore the two terms

[
y^{S(\varepsilon)}
\quad\text{and}\quad
y^{-S(\varepsilon)}
]

naturally pair into

[
q_{|S(\varepsilon)|}(t).
]

If we sum (q_{|S(\varepsilon)|}) over **all** sign vectors, every pair is counted twice. Hence

[
\boxed{
q_{\ell_1}(t)\cdots q_{\ell_c}(t)
=================================

\frac12
\sum_{\varepsilon\in{-1,+1}^c}
q_{\left|S(\varepsilon)\right|}(t).
}
]

That is where the factor (1/2) comes from.

---

## Step 5: Apply (F)

Now apply the linear functional (F) to both sides:

[
E(\ell_1,\ldots,\ell_c)
=======================

F\left(q_{\ell_1}\cdots q_{\ell_c}\right).
]

Using the previous identity,

[
E(\ell_1,\ldots,\ell_c)
=======================

F\left(
\frac12
\sum_{\varepsilon\in{-1,+1}^c}
q_{\left|S(\varepsilon)\right|}
\right).
]

By linearity of (F),

[
E(\ell_1,\ldots,\ell_c)
=======================

\frac12
\sum_{\varepsilon\in{-1,+1}^c}
F\left(q_{\left|S(\varepsilon)\right|}\right).
]

Since

[
M_s=F(q_s),
]

we obtain

[
\boxed{
E(\ell_1,\ldots,\ell_c)
=======================

\frac12
\sum_{\varepsilon\in{-1,+1}^c}
M_{\left|\sum_{r=1}^c \varepsilon_r\ell_r\right|}.
}
]

That is the formula.

---

## Example: cycle type ((3,4))

Here (c=2), (\ell_1=3), (\ell_2=4). The sign vectors are

[
(+,+),\quad (+,-),\quad (-,+),\quad (-,-).
]

The corresponding signed sums are

[
3+4=7,
]

[
3-4=-1,
]

[
-3+4=1,
]

[
-3-4=-7.
]

Taking absolute values gives

[
7,;1,;1,;7.
]

Therefore

[
E(3,4)
======

\frac12
\left(M_7+M_1+M_1+M_7\right)
============================

M_7+M_1.
]

Using

[
M_7=579,\qquad M_1=-1,
]

we get

[
E(3,4)=578.
]

---

## Example: cycle type ((2,2,2,2))

Here (c=4). The signed sums are

[
\pm2\pm2\pm2\pm2.
]

The possible absolute values are (8,4,0). Counting multiplicities:

* (|S|=8): 2 sign vectors.
* (|S|=4): 8 sign vectors.
* (|S|=0): 6 sign vectors.

So

[
E(2,2,2,2)
==========

\frac12
\left(2M_8+8M_4+6M_0\right).
]

Thus

[
E(2,2,2,2)
==========

M_8+4M_4+3M_0.
]

Using

[
M_8=4738,\quad M_4=2,\quad M_0=2,
]

we get

[
E(2,2,2,2)
==========

# 4738+8+6

4752.

]

So the compact formula is really saying: every cycle length (\ell_r) contributes a choice of sign, and the full extension count is the average, over all signed sums of the cycle lengths, of the corresponding formal one-cycle count (M_s).
